# Purpose: Take automatic generated reports from Ansys Workbench
#          and purge all except certain tables and figures,
#          and swap figure captions figures.
#          Images (static) are not retained, cause they don't
#          update anyway, can be added as unique figure.
#
# Author: Duco Chapelle
# Date: 2017-07-06

from lxml import html

def text(element):
    return element if element.text else text(element.getchildren()[0])
    
def keep(element, items, endings):
    e = text(element)
    if e.text in items:
        return True
    elif e.text_content().endswith(endings):
        return True
    else:
        return False

def remove(element):
    element.getparent().remove(element)

def purge(body, tabfig, endings, sections):
    # this is getting out of control
    second_element = False
    greenlight = False
    last_caption, last_kind = None, None
    for element in body.getchildren():
        if element.tag == "h2":
            if text(element).text.startswith("Eigenvalue Buckling"):
                endings = tuple(e for e in endings if e != "Results")
        if greenlight:                                      # LOGIC A = sections
            continue                                        # LOGIC A                                 
        elif second_element:                                    # LOGIC B = tabfig, endings                  
            remove(element)                                     # LOGIC B            
            second_element = False                              # LOGIC B             
        elif element.tag in ["h2", "h3", "h4"]:             # LOGIC A
            if element.getchildren()[0].text in sections:   # LOGIC A
                if greenlight:                              # LOGIC A
                    greenlight = False                      # LOGIC A
                else:                                       # LOGIC A
                    greenlight = True                       # LOGIC A
        elif element.get("class")=="caption":                   # LOGIC B
            if not keep(element, tabfig, endings):              # LOGIC B
                # unless its a table of a changing load!
                kind = text(element).text.split(" ")[0]                             # LOGIC C = tables with varying loads...
                caption = ''.join(text(element).text_content().split("\r\n")[1:])   # LOGIC C = ook tables van buckling? :D            
                if not (kind == "TABLE" and last_kind == "FIGURE" and caption == last_caption): # LOGIC C
                    remove(element)                             # LOGIC B
                    second_element = True                       # LOGIC B
            last_caption = caption                                                  # LOGIC C
            last_kind = kind                                                        # LOGIC C

    return body

def emptyheaders(body):
    last_element = None
    for element in body.getchildren():
        if element.tag in ["h2", "h3", "h4"]:
            if last_element.tag in ["h2", "h3", "h4"]:
                if int(last_element.tag[1]) >= int(element.tag[1]):
                    remove(last_element)
        last_element = element
    return body

def swap(body):
    last_element = None
    for element in body.getchildren():
        if element.get("class")=="figure":
            body.remove(last_element)
            body.insert(body.index(element)+1, last_element)
        last_element = element
    return body

def rename(filename, n):
    *head, tail = filename.split(".")
    name = str(n)+"." + tail
    for s in reversed(head):
        name = s + name
    return name

def modify(filename):
    global tree
    tree = html.parse(filename)

    remove(tree.xpath('//div[@id="Contents"]')[0])
    remove(tree.xpath('//div[@id="TableOfContents"]')[0])

    headers = ["Coordinate Systems", "Units"] # retain entirely
    itemsByNumber = [f"TABLE {t}" for t in []]+[f"FIGURE {f}" for f in []] # retain by caption number
    captionEndings = ('Body Groups', # retain by typical caption
            'Contact Regions',
            'Mesh',
            'Step-Specific "Step Controls"',
            'Accelerations',
            'Loads',
            'Results',
            'Initial Condition',
            'Figure')+tuple(f"Figure {i}" for i in range(99))

    
    swap(emptyheaders(purge(tree.xpath(
        '//div[@id="Body"]')[0],
        itemsByNumber,
        captionEndings,
        headers
    )))

    tree.write(rename(filename,2), method='html') # , encoding='UTF-8')

    # xml write to file fucks my links up
    with open(rename(filename,2), 'r') as f2:
        with open(rename(filename,3), 'w') as f3:
            for line in f2:
                f3.write(line.replace("%5C","\\"))

if __name__ == "__main__":
    modify('Mechanical_Report.htm')
