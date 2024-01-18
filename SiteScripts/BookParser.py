import regex
from GutenReaderApp import models as my_models
from django.db import models


def parse_file(txt_file):
    if type(txt_file) != models.FileField:
        return False

    Book_Str = txt_file.read()
    # file = open("Alice.txt", "r")
    # Book_Str = file.read()
    # file.close()
    # Author and Translator as optional meta fields
    # only show Translator if applicable, Use "Unknown" for no author
    Meta = ["Title: ", "Author: ", "Translator: ", "Language: "]
    for i in range(len(Meta)):
        i_position = Book_Str.find(Meta[i])
        if i_position == -1:
            Meta[i] = ""
        else:
            Meta[i] = Book_Str[i_position + len(Meta[i]):Book_Str.find("\n", i_position)]
    # print(Meta)

    Book_Lines = Book_Str.splitlines()
    Contents_Start = get_contents_start(Book_Lines)
    Chapter_Names = get_chapter_names(Book_Lines=Book_Lines, cont_start=Contents_Start)
    # for x in Chapter_Names:
    #     print(x)
    Reg_Chapter_Names = regify(Chapter_Names)
    # for x in Reg_Chapter_Names:
    #     print(x)
    SpansList = get_chapter_spans(Reg_Chapter_Names, Book_Str)
    len_spans = len(SpansList[0])
    for spans in SpansList[0:]:  # same number of matches expected for each chapter
        if (len(spans) != len_spans):
            raise Exception("Inconsistent Number of Title Matches")
    if (len_spans <= 1):
        raise Exception("Less than two matches")
    end_match = regex.search(r"\*\*\* END OF THE PROJECT GUTENBERG", Book_Str)
    if end_match is None:
        raise Exception("Unable to find expected EOF Str")
    End_Pos = end_match.span()[0]
    Split_Positions = []
    for spans in SpansList:
        Split_Positions.append(spans[1][0])
    Split_Positions.append(End_Pos)
    title = Meta[0]
    author = "Unknown"
    if Meta[1] != "":
        Author = Meta[1]
    language = Meta[3]

    new_book = my_models.Book(title, author, language,
                              full_text=Book_Str, chapter_titles=Chapter_Names, chapter_divisions=Split_Positions)
    new_book.save()
    return True

    # print(Split_Positions)
    # print(Book_Str[Split_Positions[1]:Split_Positions[2]])


def get_chapter_spans(Reg_Chapter_Names, Book_Str):
    SpansList = []
    for chap in Reg_Chapter_Names:
        # print(chap)
        match_iterator = regex.finditer(chap, Book_Str)
        # if match_iterator is None:
        #     print(len(Book_Str))
        chap_matches = []  # same number of matches expected for each chapter
        for match in match_iterator:
            # print(match.span())
            chap_matches.append(match.span())
        SpansList.append(chap_matches)
    return SpansList


def regify(Chapter_Names):
    reg_chapter_names = []
    for name in Chapter_Names:
        reg_name = ""
        space_cnt = 0
        for char in name:
            if (char == "."):  # '.'s are used inconsistently so they are optional
                reg_name += "\.?"
            elif (char == " "):  # 2 or more spaces -> 1+ whitespace || end it there
                space_cnt += 1
                if space_cnt == 1:
                    reg_name += " "
                if space_cnt == 2:
                    reg_name = reg_name[:-1]
                    reg_name += "\s+"
            else:
                space_cnt = 0
                reg_name += char
        reg_chapter_names.append(reg_name)
    return reg_chapter_names


def get_contents_start(Book_Lines):
    Search_String = "Contents"
    cont_start = -1
    for i in range(len(Book_Lines)):  # find where table of contents starts
        cur_line = Book_Lines[i]
        found = cur_line.find(Search_String)
        if found == -1:
            found = cur_line.find(Search_String.upper())  # try uppercase version
        if found != -1:
            cont_start = i + 1
            break
    return cont_start


def get_chapter_names(cont_start, Book_Lines):
    Chapter_Names = []
    for i in range(cont_start, len(Book_Lines)):
        cur_line = Book_Lines[i]
        if cur_line.isspace() is False and cur_line != "":
            # Checks if the title of the first chapter has been reached improve
            if len(Chapter_Names) > 0 and cur_line.startswith(Chapter_Names[0][:7]):
                break
            Chapter_Names.append(cur_line.lstrip())
    return Chapter_Names
