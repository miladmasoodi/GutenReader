import unicodedata


def get_section_indices(chapter_divisions):
    section_indices = []
    for i in range(len(chapter_divisions)-1, 0, -1):
        line_difference = chapter_divisions[i] - chapter_divisions[i-1]
        if line_difference < 10:  # 10 is only based on observed line_diffs
            section_indices.append(i-1)
    section_indices.reverse()
    return section_indices

def parse_html_file(html_file):
    START_TEXT = "*** START OF"
    END_TEXT = "*** END OF"

    # assume tiny chaps are book or section titles

    toc_lines = []
    chap_titles = []
    chap_ids = []
    chap_starts = []
    meta_data = []

    raw_text = html_file.read()
    normal_text = unicodedata.normalize("NFKD", raw_text)
    lines = normal_text.splitlines()

    start_line = find_line_of_value(lines, START_TEXT)
    end_line = find_line_of_value(lines, END_TEXT)
    head_end_line = find_line_of_value(lines, "</head>")
    if end_line == -1 or start_line == -1:
        raise Exception("Document does not follow expected formatting")

    # lines = lines[start_line:] # must be after meta portion
    meta_portion = ''.join(lines[head_end_line + 1:start_line])
    TITLE_SAMPLE = "<strong>Title</strong>: "
    AUTHOR_SAMPLE = "<strong>Author</strong>: "
    LANG_SAMPLE = "<strong>Language</strong>: "
    meta_samples = [TITLE_SAMPLE, AUTHOR_SAMPLE, LANG_SAMPLE]
    meta_values = ["Title not found", "Unknown Author", "Language not found"]
    for index, sample in enumerate(meta_samples):
        sample_position = meta_portion.find(sample)
        offset = len(sample)
        start_position = sample_position + offset
        end_position = meta_portion[start_position:].find("<") + start_position
        meta_values[index] = meta_portion[start_position:end_position]

    print(meta_values)
    end_of_toc = find_line_of_value(lines, "<!--end chapter-->")

    toc_lines = find_all_lines_of_value(lines[:end_of_toc], 'href="#')



    # to see if it started counting non-toc <a>'s
    toc_lines = revise_toc_lines(toc_lines)

    chap_ids = find_id_values(lines, toc_lines)
    chap_starts = find_ch_start_lines(lines, chap_ids)
    chap_starts.append(end_line)

    chap_titles = find_chap_titles(lines, toc_lines)
    print(chap_titles)
    print(chap_ids)
    print(chap_starts)

    # # split into diff strings before reformating so chap positions aren't lost
    # chap_portions = []
    # prev_index = 0
    # for i in range(1, len(chap_starts)):
    #     chap_portions.append(lines[chap_starts[prev_index]:chap_starts[i]])
    #     prev_index = i

    # new_book = my_models.Book(title=meta_values[0], author=meta_values[1], language=meta_values[2],
    #                           full_text='\n'.join(lines), chapter_titles=chap_titles, chapter_divisions=chap_starts)
    # new_book.save()
    book_dict = {"meta_values": meta_values, "full_text": '\n'.join(lines),
                 "chapter_titles": chap_titles, "chapter_divisions": chap_starts}
    return book_dict


def revise_toc_lines(toc_lines):
    avg_diff = (toc_lines[-1] - toc_lines[0]) / (0.0 + len(toc_lines))
    first_diff = toc_lines[1] - toc_lines[0]
    line_diff = abs(first_diff - avg_diff)
    if line_diff > first_diff / 4.0:  # denom might need to be much higher
        print("Unexpected line difference: " + str(line_diff) + " avg: " + str(avg_diff))
        old_sum = first_diff
        for i in range(2, len(toc_lines)):
            new_diff = toc_lines[i] - toc_lines[i-1]
            new_sum = old_sum + new_diff
            old_avg_diff = old_sum / (i-1)
            old_sum = new_sum
            if abs(old_avg_diff - new_diff) > old_avg_diff/2.0:
                return toc_lines[:i]
    return toc_lines

        # raise Exception("Unexpected line difference: " + str(line_diff) + " avg: " + str(avg_diff))


def find_line_of_value(html_lines, value):
    for index, line in enumerate(html_lines):
        if value in line:
            return index
    return -1


def find_all_lines_of_value(html_lines, value):
    line_indices = []
    for index, line in enumerate(html_lines):
        if value in line:
            line_indices.append(index)
    return line_indices


def find_ch_start_lines(html_lines, ch_ids):
    chap_starts = []
    # find all ids first to limit comparisons to ch_ids
    id_lines = find_all_lines_of_value(html_lines, 'id="')
    for line_index in id_lines:
        cur_line = html_lines[line_index]
        for id in ch_ids:
            if id in cur_line:
                chap_starts.append(line_index)
    return chap_starts


def find_id_values(html_lines, result):
    id_values = []
    sample = 'href="#'
    for i in result:
        cur_line = html_lines[i]
        start_index = cur_line.find(sample) + len(sample)
        diff = cur_line[start_index:].find('"')
        id_values.append(cur_line[start_index:start_index + diff])
    return id_values


def find_chap_titles(lines, result):
    chapter_titles = []
    for ch_line in result:
        cur_line = lines[ch_line]
        end_index = cur_line.find("</")
        start_index = -1
        for i in range(end_index - 1, 0, -1):
            if cur_line[i] == ">":
                start_index = i + 1
                break
        chapter_titles.append("" + cur_line[start_index:end_index])
    return chapter_titles



