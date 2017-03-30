# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ElementTree
import xml.etree.cElementTree as cElementTree

__all__ = ["Fdx2Fountain"]

class Fdx2Fountain():

    def lookup_type(self,ptype,fd_paragraph):
        if ptype == "Action":
            ptype = "action"
        elif ptype == "Character":
            ptype = "character"
        elif ptype == "Dialogue":
            ptype = "dialogue"
        elif ptype == "Parenthetical":
            ptype = "parenthetical"
        elif ptype == "Scene Heading":
            ptype = "sceneheader"
        elif ptype == "Shot":
            ptype = "shot"
        elif ptype == "Transition":
            ptype = "transition"
        elif ptype == "Teaser/Act One":
            ptype = "header"
        elif ptype == "New Act":
            ptype = "header"
        elif ptype == "End Of Act":
            ptype = "header"
        elif ptype == "End of Teaser":
            ptype = "header"
        elif ptype == "General":
            if fd_paragraph[0].tag == "DualDialogue":
                ptype = "dualdialogue"
            else:
                ptype = "general"
        else:
            ptype = "action"
        return ptype

    def process_text(self,fd_texts,ptype,dual=False):
        results = []
        for fd_text in fd_texts:
            text_style = fd_text.get('Style')
            if fd_text.text != None:
                #clean smart quotes
                fd_text.text = fd_text.text.replace(u"\u201c", "\"").replace(u"\u201d", "\"") #strip double curly quotes
                fd_text.text  = fd_text.text.replace(u"\u2018", "'").replace(u"\u2019", "'").replace(u"\u02BC", "'") #strip single curly quotes
                if "FADE IN:" in fd_text.text.upper():
                    fd_text.text = fd_text.text.upper()
                if ptype in ["character","transition","sceneheader","header","shot"]:
                    fd_text.text = fd_text.text.upper()
                    if ptype in ["character"] and dual:
                        fd_text.text = fd_text.text + " ^"
                    if ptype in ["header"]:
                        fd_text.text = ">**" + fd_text.text + "**<"
                    if ptype in ["transition"] and not fd_text.text.upper().endswith("TO:"):
                        fd_text.text = "> " + fd_text.text
                    if len(results) == 0 or results[0] != {"style":"","text":"\n"}:
                        results.insert(0,{"style":"","text":"\n"})
                if ptype in ["action"]:
                    fd_text.text = fd_text.text
                    if len(results) == 0 or results[0] != {"style":"","text":"\n"}:
                        results.insert(0,{"style":"","text":"\n"})
                results.append({"style":text_style,"text":fd_text.text})
        return results

    def fountain_from_fdx(self,fdx_string,start_with_scene=False,end_with_scene=False):
        theoutput = u""
        fd_doc = cElementTree.fromstring(fdx_string)
        ptext = []
        scenecount = 0
        if start_with_scene == False and end_with_scene == False:
            renderParagraphs = True
        else:
            renderParagraphs = False
        for fd_content in fd_doc.findall("Content"):
            for fd_paragraph in fd_content:
                if fd_paragraph.tag == "Paragraph":
                    ptype = self.lookup_type(fd_paragraph.get('Type'),fd_paragraph)
                    if ptype == "sceneheader":
                        scenecount += 1
                        if start_with_scene != False and scenecount == start_with_scene:
                            renderParagraphs = True
                        if end_with_scene != False and scenecount == end_with_scene:
                            renderParagraphs = False
                    if renderParagraphs:
                        if ptype == "dualdialogue":
                            if len(fd_paragraph[0]) == 4:
                                ptext.append(self.process_text(fd_paragraph[0][0].findall("Text"),"character"))
                                ptext.append(self.process_text(fd_paragraph[0][1].findall("Text"),"dialogue"))
                                ptext.append(self.process_text(fd_paragraph[0][2].findall("Text"),"character",True))
                                ptext.append(self.process_text(fd_paragraph[0][3].findall("Text"),"dialogue"))
                            else:
                                print "malformed dual dialog"
                        else:
                            fd_texts = fd_paragraph.findall("Text")
                            if fd_texts != None:
                                ptext.append(self.process_text(fd_texts,ptype))

        for ptext_parts in ptext:
            content = []
            for block in ptext_parts:
                if block["style"] == "Italic":                
                    content.append("*" + block["text"] + "*")
                elif block["style"] == "Underline":
                    content.append("_" + block["text"] + "_")
                elif block["style"] == "Bold":
                    content.append("**" + block["text"] + "**")
                elif block["style"] == "Bold+Underline":
                    content.append("_**" + block["text"] + "**_")
                elif block["style"] == "Italic+Underline":
                    content.append("_*" + block["text"] + "*_")
                else:
                    content.append(block["text"])
            theoutput += u"".join(content) + "\n"

        return theoutput
