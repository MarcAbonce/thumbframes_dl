"""
Takes a video with a "Space opera" style opening crawl and prints its text.
"""
from sys import path
from os.path import realpath, dirname
path.append(realpath(dirname(realpath(__file__)) + '/../'))

from difflib import SequenceMatcher
from statistics import median

import cv2
import numpy as np
import pytesseract
from enchant import Dict
from enchant.checker import SpellChecker

from thumbframes_dl import YouTubeFrames


# Never Tell Me the Odds - Star Noirs One-off opening crawl | Saving Throw | CC BY 3.0
VIDEO_URL = 'https://www.youtube.com/watch?v=kEVOHhFg_s4'

LANG = ('en', 'eng')
dictionary = Dict(LANG[0])
spellchecker = SpellChecker(LANG[0])


# pytesseract.image_to_string returns a nice string, but no confidence level,
# pytesseract.image_to_data dumps this whole mess, so you have to parse it
def parse_pytesseract_output(data):

    # this list is a mix of ints as numbers and ints as strings
    data['conf'] = [int(num) for num in data['conf']]

    # only return line if confidence is high enough
    def _get_line_if_confident(start_index, end_index=None):
        if len(data['conf'][start_index:end_index]) == 0:
            return
        if median(data['conf'][start_index:end_index]) >= 70:
            return ' '.join(data['text'][start_index:end_index])

    text = []
    prev_line_num = 0
    line_index = 0
    # each text entry has a corresponding line_num and that's how you find newlines
    for i in range(len(data['text'])):
        if prev_line_num != data['line_num'][i]:
            prev_line_num = data['line_num'][i]
            text.append(_get_line_if_confident(line_index, i + 1))
            line_index = i + 1
    text.append(_get_line_if_confident(line_index, None))
    text = list(filter(None, text))
    return text


# get list of every line of text extracted from image
def extract_text_from_frames(thumbframes_image):
    # convert raw image's bytes to opencv image object
    image = np.asarray(bytearray(thumbframes_image.get_image()), dtype='uint8')
    image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)

    # set black text on white background
    image = cv2.bitwise_not(image)

    w_step = thumbframes_image.width // thumbframes_image.cols
    h_step = thumbframes_image.height // thumbframes_image.rows
    scanned_texts = []
    for i in range(thumbframes_image.rows):
        for j in range(thumbframes_image.cols):
            # crop single frame from image
            frame = image[i*h_step:(i+1)*h_step-1, j*w_step:(j+1)*w_step-1]

            # crop bottom half of image (where crawling text is more visible) and try to straighten the text
            crop_side = w_step // 5
            crop_top = h_step // 2
            src_box = np.array([[crop_side, crop_top],
                                [w_step - crop_side, crop_top],
                                [0, h_step],
                                [w_step, h_step]],
                               np.float32)
            dst_box = np.array([[0, 0], [w_step, 0], [0, h_step], [w_step, h_step]], np.float32)
            matrix = cv2.getPerspectiveTransform(src_box, dst_box)
            text_area = cv2.warpPerspective(frame, matrix, (w_step, h_step))

            # pytesseract works better with bigger images
            text_area = cv2.resize(text_area, (w_step*5, h_step*5))

            # extract frame's text
            scanned_output = pytesseract.image_to_data(text_area,
                                                       lang=LANG[1],
                                                       config='--psm 6',
                                                       output_type=pytesseract.Output.DICT)
            scanned_lines = parse_pytesseract_output(scanned_output)
            scanned_texts.append([line for line in scanned_lines if line != '' and not line.isspace()])

            # cv2.imshow('', text_area); cv2.waitKey(0)

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
            spelling_score = get_spelling_score(line)

            # check if line is a likely duplicate
            best_line = None
            best_similarity = 0
            for i, saved_line in enumerate(complete_text):
                similarity = SequenceMatcher(None, line, saved_line).ratio()
                if similarity >= 0.7 and similarity > best_similarity:
                    best_line = i
                    best_similarity = similarity

            # append new line if unique, otherwise merge with similar line
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
    video = YouTubeFrames(VIDEO_URL)

    scanned_texts = []
    for thumbframes_image in video.get_thumbframes():
        scanned_texts += extract_text_from_frames(thumbframes_image)

    video_text = merge_extracted_texts(scanned_texts)
    print(video_text)
