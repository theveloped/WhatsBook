#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from builtins import input

import argparse
import io
import sys
import re
import os
import datetime

from PIL import Image, ImageFont, ImageDraw
import numpy as np

import random
from wordcloud import WordCloud


lineAppendix = ""
nameType = "\\textbf{"
spacing = 0.01
maxHeight = 0.8 # with regard to textwidth
urlRegex = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
pageWidth = 1480
pageHeight = 2100
lineWidth = 40


def main():
  # Start guided setup if no arguments are parsed
  if len(sys.argv) == 1:
    print("""
 _       ____          __       ____              __  
| |     / / /_  ____ _/ /______/ __ )____  ____  / /__
| | /| / / __ \/ __ `/ __/ ___/ __  / __ \/ __ \/ //_/
| |/ |/ / / / / /_/ / /_(__  ) /_/ / /_/ / /_/ / ,<   
|__/|__/_/ /_/\__,_/\__/____/_____/\____/\____/_/|_|  

Script to convert exported whatsApp chat to a parsed 
LaTeX file for printing. Call using arguments or without
to follow the guided setup.
""")
    arguments = argparse.Namespace()

    print("[+] Enter the directory exported from whatsApp:")
    arguments.chatDir = input(">> ")
    print("")

    print("[+] Enter the output path:")
    arguments.output = [input(">> ")]
    print("")

    print("[+] Would you like to generate wordclouds as chapters? Y/N:")
    arguments.cloud = ("y" in input(">> ").lower())
    print("")

  # Parse arguments for single line execution 
  else:
    arguments = parseArguments()

  # open file
  if arguments.output:

    # Add file extension
    if not arguments.output[0][-4:] == ".tex":
      arguments.output[0] += ".tex"

    with open(arguments.output[0], "w") as resultObj:
      parsedChat = parseChat(arguments)

      for line in parsedChat:
        resultObj.write(line + "\n")

  else:
    parsedChat = parseChat(arguments)

    for line in parsedChat:
      print(line, file=sys.stdout)


def parseArguments():
  parser = argparse.ArgumentParser(description="")

  # Required arguments
  parser.add_argument("chatDir", help="</chatDir>, directory containing chat export")

  # Optional key value pairs
  parser.add_argument("-o", "--output", nargs=1, help="[/outputFile.tex], file to write output to")

  # Optional flags
  parser.add_argument("-c", "--cloud", action="store_true", help="generate section wordclouds")

  return parser.parse_args()


def parseChat(arguments):
  pics = []
  picsDate = []
  picsSender = []
  aspectRatios = []
  names = {}
  senders = []
  prevDate = None
  prevMonth = None
  spaceLeft = True
  sectionNr = 0
  monthText = ""
  lineAppendix = ""

  # Start parsing of main file
  chatPath = os.path.join(arguments.chatDir, "_chat.txt")

  with open(chatPath, "r") as fileObj:
    for line in fileObj.readlines():  
      # Strip line
      line = line.strip()

      # Skip empty lines
      if line in ["", "\n", "\r\n", "\r"]:
        continue


      try:
        # Remove timestamp
        if not re.search("\d{2}:\d{2}:\d{2}:\s", line):
          raise

        line = re.sub("\d{2}:\d{2}:\d{2}:\s", "", line)

        # Remove and store date
        date, line = line.split(" ", 1)

        # Remove and store sender
        sender, line = line.split(": ", 1)
        sender = sender.strip()

      except:
        line = parseText(line)
        lineAppendix += line + "\\\\"
        
        continue


      # Parse names
      if not sender in names:

        if len(sys.argv) == 1:
          print("[+] What would you like " + sender + " to be called \n(leave blank to keep default):", file=sys.stderr)
          senderName = input(">> ")
          print("")

          if senderName:
            names[sender] = nameType + senderName + "}"
          else:
            names[sender] = nameType + sender + "}"

        else:
          names[sender] = nameType + sender + "}"


      # Handle pictures
      pic = re.search("([a-zA-Z0-9-_]+).jpg", line)
      
      if pic:
        pic = pic.group(0)
        picPath = os.path.join(arguments.chatDir, pic)

        try:
          with Image.open(picPath) as img:
            width, height = img.size
            aspectRatios.append(float(width)/height)

            pics.append(pic)
            picsDate.append(date)
            picsSender.append(sender)
        except:
          print("[!] Image file not found: " + picPath, file=sys.stderr)



        # Plot if two are available
        if len(pics) == 2:
          figureString = ""

          if spaceLeft == (aspectRatios[0] <  aspectRatios[1]):
              width1 = aspectRatios[0] / (aspectRatios[0] + aspectRatios[1]) - spacing/2
              width2 = aspectRatios[1] / (aspectRatios[0] + aspectRatios[1]) - spacing/2

              height = width1 / aspectRatios[0]

              picPath1 = os.path.join(arguments.chatDir, pics[0])
              picPath2 = os.path.join(arguments.chatDir, pics[1])

          else:
              width1 = aspectRatios[1] / (aspectRatios[0] + aspectRatios[1]) - spacing/2
              width2 = aspectRatios[0] / (aspectRatios[0] + aspectRatios[1]) - spacing/2

              height = width1 / aspectRatios[1]

              picPath1 = os.path.join(arguments.chatDir, pics[1])
              picPath2 = os.path.join(arguments.chatDir, pics[0])

              picsDate = picsDate[::-1]
              picsSender = picsSender[::-1]

          figureString += ("\\begin{figure}[htp]\n" + 
                          "\t\\centering\n" + 
                          "\t\\includegraphics[width=" + str(width1) + "\\textwidth, height=" + str(height) + "\\textwidth]{" + picPath1 + "}\\hfill\n" +
                          "\t\\includegraphics[width=" + str(width2) + "\\textwidth, height=" + str(height) + "\\textwidth]{" + picPath2 + "}\n" +
                          "\t\\caption{{\\footnotesize" + picsDate[0] + " by " + names[picsSender[0]] + ", " + picsDate[1] + " by " + names[picsSender[1]] + "}}\n" +
                          "\\end{figure}\n")

          spaceLeft = not spaceLeft

          pics = []
          picsDate = []
          picsSender = []
          aspectRatios = []

          yield figureString

        # Continue after handling image
        continue


      # Remove unsupported attachments
      if "<‎attached>" in line:
        print("[!] Unsupported attachment found: " + line, file=sys.stderr)
        continue

      # Parse text in line
      line = parseText(line)


      # Sort by day
      if not date == prevDate:
        parsedDate, month = parseDate(date)

        if len(pics) == 1:
            figureString = ""

            width = min([maxHeight * aspectRatios.pop() / 1, 1])
            picPath = os.path.join(arguments.chatDir, pics.pop())

            figureString += ("\\begin{figure}[htp]\n" + 
                            "\t\\centering\n" + 
                            "\t\\includegraphics[width=" + str(width) + "\\textwidth]{" + picPath + "}\n" +
                            "\t\\caption{{\\footnotesize" + picsDate.pop() + " by " + names[picsSender.pop()] + "}}\n" +
                            "\\end{figure}\n")

            yield figureString


        if not month == prevMonth: 
          monthImgPath = os.path.join(arguments.chatDir, "sectionImage_" + str(sectionNr) + ".png")

          if monthText and arguments.cloud:
              img = Image.new("L", (pageWidth, pageHeight), 0)
              img = drawMonth(img, prevMonth, mask=True)
              mask = np.array(img)

              wordcloud = WordCloud(background_color="white", max_font_size=200, relative_scaling=.75, mask=mask)
              wordcloud.generate(monthText)
              wordcloud.recolor(color_func=grey_color_func, random_state=3)
              wordcloud.to_file(monthImgPath)

              img = Image.open(monthImgPath)

          else:
              img = Image.new("L", (pageWidth, pageHeight), 255)

          # if monthText:
          if prevMonth:
            img = drawMonth(img, prevMonth, mask=False)
            img.save(monthImgPath)

          # Write section line of upcoming month
          monthImgPath = os.path.join(arguments.chatDir, "sectionImage_" + str(sectionNr + 1) + ".png")
          yield "\n\picturechapter{%s}{%s}" % (month, monthImgPath)

          monthText = ""
          sectionNr += 1
          prevMonth = month


        prevDate = date
        yield "\section*{%s}" % parsedDate


      # Return standard line
      yield lineAppendix + names[sender] + ": " + line + "\\\\"
      monthText += lineAppendix + line + "\n"
      lineAppendix = ""


    # generate final month image
    monthImgPath = os.path.join(arguments.chatDir, "sectionImage_" + str(sectionNr) + ".png")

    if arguments.cloud:
        img = Image.new("L", (pageWidth, pageHeight), 0)

        img = drawMonth(img, prevMonth, mask=True)
        mask = np.array(img)

        wordcloud = WordCloud(background_color="white", max_font_size=200, relative_scaling=.75, mask=mask)
        wordcloud.generate(monthText)
        wordcloud.recolor(color_func=grey_color_func, random_state=3)
        wordcloud.to_file(monthImgPath)

        img = Image.open(monthImgPath)
        img = drawMonth(img, prevMonth, mask=False)
        img.save(monthImgPath)

    else:
        img = Image.new("L", (pageWidth, pageHeight), 255)
        img = drawMonth(img, prevMonth, mask=False)
        img.save(monthImgPath)


def drawMonth(img, month, mask=False):
  font = ImageFont.truetype("Chivo-Black.otf", 200)

  draw = ImageDraw.Draw(img)
  width, height = draw.textsize(month.upper(), font)

  x = round((pageWidth - width)/2)
  y = round((pageHeight - height)/2)

  if mask:
    draw.text((x, y - lineWidth), month.upper(), 255, font=font)
    draw.line([x, y + height, x + width, y + height], 255, width=lineWidth)

  else:
    draw.text((x, y - lineWidth), month.upper(), 0, font=font)
    draw.line([x, y + height, x + width, y + height], 0, width=lineWidth)

  return img


def grey_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return "hsl(0, 0%%, %d%%)" % random.randint(40, 100)


def parseText(line):
    # Replace url
    url = re.search(urlRegex, line)
    if url:
        url = url.group(0)
        line = line.replace(url, "URL")

    # Replace latex characters
    line = re.sub("\\\\", "\\\\\\\\", line)
    line = re.sub("&", "\&", line)
    line = re.sub("\$", "\$", line)
    line = re.sub("#", "\#", line)
    line = re.sub("%", "\%", line)
    # line = re.sub('"', "``", line)
    # line = re.sub("'", "``", line)
    line = re.sub("\^", "\textrm", line)
    line = re.sub("/", "\/", line)

    # repair URL tag
    if url:
        line = re.sub("URL", "\\url{" + url + "}", line)

    return line


def parseDate(dateString):
    # 29/12/15
    day, month, year = re.split("[-/]", dateString, 2)
    date = datetime.date(int("20" + year), int(month), int(day))

    if 4 <= int(day) <= 20 or 24 <= int(day) <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][int(day) % 10 - 1]

    parsedDate = date.strftime('%A') + " $" + day + "\\textsuperscript{" + suffix + "}$"
    return (parsedDate, date.strftime("%B"))


if __name__ == '__main__':
  main()