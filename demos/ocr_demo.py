from sys import path
from os.path import realpath, dirname
path.append(realpath(dirname(realpath(__file__)) + '/../'))

from difflib import SequenceMatcher

import cv2
import numpy as np
import pytesseract
from enchant import Dict
from enchant.checker import SpellChecker
from requests import get

from thumbframes_dl import YouTubeFrames


LANG = ('en', 'eng')
dictionary = Dict(LANG[0])
spellchecker = SpellChecker(LANG[0])


# get list of every line of text extracted from image
def extract_text_from_frames(image, width, height, cols, rows):
    # convert raw image's bytes to opencv image object
    image = np.asarray(bytearray(image), dtype='uint8')
    image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)

    w_step = width // cols
    h_step = height // rows
    scanned_texts = []
    for i in range(rows):
        for j in range(cols):
            # crop single frame from image
            frame = image[i*h_step:(i+1)*h_step-1, j*w_step:(j+1)*w_step-1]

            # set black text on white background
            frame = cv2.bitwise_not(frame)

            # crop bottom half of image (where crawling text is more visible) and try to straighten the text
            src_box = np.array([[20, 60], [140, 60], [0, 90], [160, 90]], np.float32)
            dst_box = np.array([[0, 0], [160, 0], [0, 90], [160, 90]], np.float32)
            matrix = cv2.getPerspectiveTransform(src_box, dst_box)
            text_area = cv2.warpPerspective(frame, matrix, (w_step, h_step))

            # pytesseract works better with bigger images
            text_area = cv2.resize(text_area, (w_step*5, h_step*5))

            # extract frame's text
            scanned_lines = pytesseract.image_to_string(text_area, lang=LANG[1], config='--psm 6').split('\n')
            scanned_texts.append([line for line in scanned_lines if line != '' and not line.isspace()])

            # cv2.imshow('', text_area)
            # cv2.waitKey(0)

    return scanned_texts


# get 0 to 1 score where 1 means perfect spelling
def get_spelling_score(line):
    spellchecker.set_text(line)
    misspellings = [err.word for err in spellchecker]
    return 1 - len(misspellings) / len(line.split())


# merge duplicate lines of text and try to get lines with the best possible spelling
def merge_extracted_texts(scanned_texts):
    complete_text = []
    spelling_scores = []
    # read each scanned frame
    for text in scanned_texts:
        # read each line of text
        for line in text:

            # ignore if line has too many misspellings
            spelling_score = get_spelling_score(line)
            lowercase_spelling_score = get_spelling_score(line.lower())
            if spelling_score < 0.7 or lowercase_spelling_score < 0.5:
                continue

            # ignore if line is just a short sequence of really short strings
            if len(line.split()) < 5 and all([len(word) < 5 for word in line.split()]):
                continue

            # check if line is a likely duplicate
            best_line = None
            best_similarity = 0
            for i, saved_line in enumerate(complete_text):
                similarity = SequenceMatcher(None, line, saved_line).ratio()
                if similarity >= 0.75 and similarity > best_similarity:
                    best_line = i
                    best_similarity = similarity

            # append new line if unique or merge with similar line
            if best_line is None:
                complete_text.append(line)
                spelling_scores.append(spelling_score)
            else:
                new_words = line.split()
                old_words = complete_text[best_line].split()
                # if both lines have the same length, compare spellings word by word to create the best possible line
                if len(new_words) == len(old_words):
                    best_words = []
                    for i, _ in enumerate(old_words):
                        if dictionary.check(new_words[i]) and not dictionary.check(old_words[i]):
                            best_words.append(new_words[i])
                        else:
                            best_words.append(old_words[i])
                    complete_text[best_line] = ' '.join(best_words)
                    spelling_scores[best_line] = get_spelling_score(complete_text[best_line])

                elif spelling_score > spelling_scores[best_line]:
                    # replace similar looking line if the newer one has better spelling
                    complete_text[best_line] = line
                    spelling_scores[best_line] = spelling_score

    return '\n'.join(complete_text)


if __name__ == "__main__":
    # Never Tell Me the Odds | Saving Throw | CC BY 3.0
    frames = YouTubeFrames('https://www.youtube.com/watch?v=kEVOHhFg_s4')

    scanned_texts = []
    for storyboard in frames.thumbframes['L2']:
        response = get(storyboard['url'])
        response.raise_for_status()

        width, height, cols, rows = storyboard['width'], storyboard['height'], storyboard['cols'], storyboard['rows']
        scanned_texts += extract_text_from_frames(response.content, width, height, cols, rows)

    video_text = merge_extracted_texts(scanned_texts)
    print(video_text)
