indentStart = -1
tabCount = 0
def parseLine(line, curIndex):
    global indentStart
    global tabCount
    final_res = {
        'curIndex': curIndex,
        'requests': []
    }
    openPlain = 0
    openItalics = -1
    openBold = -1
    openImage = [-1, -1]
    openLink = [-1, -1]
    i = 0
    if(i == 0 and line[i] == '#'):
        counter = 1
        i += 1
        while(i < len(line) and line[i] == '#'):
            counter += 1
            i += 1
        if(line[i] == ' '):
            # TODO: Change handleHeader to just append the styling at the end
            res = handleHeader(line[i+1:len(line)], final_res['curIndex'], counter)
            final_res['curIndex'] = res['curIndex']
            final_res['requests'] += res['requests']
            return final_res
    if(i == 0 and line[i] != '\t' and indentStart > -1):
        res = endIndent(indentStart, final_res['curIndex'], tabCount)
        final_res['curIndex'] = res['curIndex']
        final_res['requests'] += res['requests']
        indentStart = -1
        tabCount = 0
    if(i == 0 and line[i] == '\t'):
        if(indentStart == -1):
            indentStart = final_res['curIndex']
        while(i < len(line) and line[i] == '\t'):
            tabCount += 1
            i += 1
        line = line[1:]
        tabCount -= 1

    for i in range(len(line)):
        c = line[i]
        if(c == '\n'):
            res = handlePlainText(line[openPlain:i+1], final_res['curIndex'])
            final_res['curIndex'] = res['curIndex']
            final_res['requests'] += res['requests']
        if(c == '*' and not (i+1 < len(line) and line[i+1] == '*') and not (i-1 >= 0 and line[i-1] == '*')):
            if(openItalics == -1):
                openItalics = i+1
            elif(openItalics > -1):
                # Closing out previous open
                res = handlePlainText(line[openPlain:openItalics-1], final_res['curIndex'])
                final_res['curIndex'] = res['curIndex']
                final_res['requests'] += res['requests']

                res = handleItalics(line[openItalics:i], final_res['curIndex'])
                final_res['curIndex'] = res['curIndex']
                final_res['requests'] += res['requests']
                i += 1
                openPlain = i
                openItalics = -1
        if(c == '*' and (i+1 < len(line) and line[i+1] == '*')):
            i += 1
            if(openBold == -1):
                openBold = i+1
            elif(openBold > -1):
                # Closing out previous open
                res = handlePlainText(line[openPlain:openBold-2], final_res['curIndex'])
                final_res['curIndex'] = res['curIndex']
                final_res['requests'] += res['requests']

                res = handleBold(line[openBold:i-1], final_res['curIndex'])
                final_res['curIndex'] = res['curIndex']
                final_res['requests'] += res['requests']
                i += 1
                openPlain = i
                openBold = -1
        if(c == '!' and (i+1 < len(line) and line[i+1] == '[')):
            i += 1
            openImage[0] = i+1
        if(c == '[' and (i-1 > 0 and line[i-1] != '!')):
            openLink[0] = i+1
        if(c == ']'):
            if(i+1 < len(line) and line[i+1] == '('):
                i += 1
                if(openLink[0] > -1):
                    openLink[1] = i+1
                if(openImage[0] > -1):
                    openImage[1] = i+1
            else:
                openLink[0] = -1
                openImage[0] = -1
        if(c == ')'):
            if(openLink[1] > -1):
                #Handle link
                # Closing out previous open
                res = handlePlainText(line[openPlain:openLink[0]-1], final_res['curIndex'])
                final_res['curIndex'] = res['curIndex']
                final_res['requests'] += res['requests']

                link_text = line[openLink[0]:openLink[1]-2]
                link_link = line[openLink[1]:i]
                res = handlePlainText(link_text, final_res['curIndex'])
                final_res['requests'] += res['requests']
                final_res['requests'].append(linkify(final_res['curIndex'], res['curIndex'], link_link))
                final_res['curIndex'] = res['curIndex']

                i += 1
                openPlain = i
                openLink[0] = -1
                openLink[1] = -1
            if(openImage[1] > -1):
                #Handle image
                # Closing out previous open
                res = handlePlainText(line[openPlain:openImage[0]-2], final_res['curIndex'])
                final_res['curIndex'] = res['curIndex']
                final_res['requests'] += res['requests']

                image_text = line[openImage[0]:openImage[1]-2]
                image_image = line[openImage[1]:i]
                res = handlePlainText("<image[{}]({})>".format(image_text, image_image), final_res['curIndex'])
                final_res['requests'] += res['requests']
                final_res['curIndex'] = res['curIndex']

                i += 1
                openPlain = i
                openImage[0] = -1
                openImage[1] = -1
    return final_res
def handlePlainText(text, curIndex):
    if(text == ""):
        return {
            'curIndex': curIndex,
            'requests': []
        }
    reqs = [{
        'insertText': {
            'text': text,
            'location': {
                'index': curIndex
            }
        }
    },
    {
        'updateTextStyle': {
            'range': {
                'startIndex': curIndex,
                'endIndex': curIndex+len(text)
            },
            'fields': "*"
        }
    }]
    curIndex += len(text)
    return {
        'curIndex': curIndex,
        'requests': reqs
    }
def handleHeader(text, curIndex, headerCount):
    res = handlePlainText(text, curIndex)
    named_style_type = 'NORMAL_TEXT'
    match headerCount:
        case 1:
            named_style_type = 'HEADING_1'
        case 2:
            named_style_type = 'HEADING_2'
        case 3:
            named_style_type = 'HEADING_3'
        case 4:
            named_style_type = 'HEADING_4'
    res['requests'].append({
        'updateParagraphStyle': {
            'paragraphStyle': {
                'namedStyleType': named_style_type
            },
            'range': {
                'startIndex': curIndex,
                'endIndex': res['curIndex']
            },
            'fields': "*"
        }
    })
    return res
def endIndent(indentStart, curIndex, tabCount):
    reqs = [{
        'createParagraphBullets': {
            'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE',
            'range': {
                'startIndex': indentStart,
                'endIndex': curIndex
            },
        }
    }]
    return {
        'curIndex': curIndex-tabCount,
        'requests': reqs
    }
def handleItalics(text, curIndex):
    res = handlePlainText(text, curIndex)
    res['requests'].append({
        'updateTextStyle': {
            'textStyle': {
                'italic': True
            },
            'range': {
                'startIndex': curIndex,
                'endIndex': res['curIndex']
            },
            'fields': "italic"
        }
    })
    return res
def handleBold(text, curIndex):
    res = handlePlainText(text, curIndex)
    res['requests'].append({
        'updateTextStyle': {
            'textStyle': {
                'bold': True
            },
            'range': {
                'startIndex': curIndex,
                'endIndex': res['curIndex']
            },
            'fields': "bold"
        }
    })
    return res
def linkify(startIndex, endIndex, link):
    return {
        'updateTextStyle': {
            'textStyle': {
                'link': {
                    'url': link
                }
            },
            'range': {
                'startIndex': startIndex,
                'endIndex': endIndex
            },
            'fields': "link"
        }
    }
