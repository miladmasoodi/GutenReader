import unicodedata


def get_section_indices(chapter_divisions):
    # assume tiny chaps are book or section titles
    section_indices = []
    for i in range(len(chapter_divisions) - 1, 0, -1):
        line_difference = chapter_divisions[i] - chapter_divisions[i - 1]
        if line_difference < 10:  # 10 is only based on observed line_diffs
            section_indices.append(i - 1)
    section_indices.reverse()
    return section_indices


def parse_html_file(html_file):
    # parse desired data from a gutenburg project book html file
    # return: dict of: meta_values, full_text, chap_titles, chap_starts, section_indices, meta_tags, pg_id
    START_TEXT = "*** START OF"
    END_TEXT = "*** END OF"

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
    TRANSLATOR_SAMPLE = "<strong>Translator</strong>: "

    meta_samples = [TITLE_SAMPLE, AUTHOR_SAMPLE, LANG_SAMPLE, TRANSLATOR_SAMPLE]
    meta_values = ["Title not found", "Unknown Author", "Language not found", ""]
    for index, sample in enumerate(meta_samples):
        sample_position = meta_portion.find(sample)
        if sample_position != -1:
            offset = len(sample)
            start_position = sample_position + offset
            end_position = meta_portion[start_position:].find("<") + start_position
            meta_values[index] = meta_portion[start_position:end_position]
    print(meta_values)

    SUBJECT_SAMPLE = '<meta name="dc.subject" content="'
    meta_tag_start = find_line_of_value(lines, SUBJECT_SAMPLE)
    meta_portion = lines[meta_tag_start:start_line]  # same values but as a list
    meta_tags = get_meta_tags(SUBJECT_SAMPLE, meta_portion)

    PG_ID_SAMPLE = '<meta property="og:url" content="https://www.gutenberg.org/ebooks/'
    pg_id_line = find_line_of_value(lines, PG_ID_SAMPLE)
    offset = len(PG_ID_SAMPLE)
    end_position = lines[pg_id_line][offset:].find("/") + offset
    pg_id = lines[pg_id_line][offset:end_position]

    end_of_toc = find_line_of_value(lines, "<!--end chapter-->")
    if end_of_toc == -1:
        end_of_toc = 4000
    toc_lines = find_all_lines_of_value(lines[:end_of_toc], 'href="#')

    # to see if it started counting non-toc <a>'s
    toc_lines = revise_toc_lines(toc_lines)

    chap_ids = find_id_values(lines, toc_lines)
    chap_starts = find_ch_start_lines(lines, chap_ids)
    chap_titles = find_chap_titles(lines, toc_lines)
    trim_chap_titles(chap_titles)

    if len(chap_ids) < len(chap_starts):
        raise Exception("too many chap_starts")

    chap_starts.append(end_line)
    print(meta_tags)

    # split into diff strings before reformating so chap positions aren't lost
    # then remove undesired lines and/or elements
    undesirable_samples = ['href="#contents', '<img', 'href="images/']
    chap_portions = []
    for i in range(1, len(chap_starts)):
        chap_portions.append(lines[chap_starts[i-1]:chap_starts[i]])

    for chapter in chap_portions:
        for undesirable_sample in undesirable_samples:
            lines = find_all_lines_of_value(chapter, undesirable_sample)
            for line in lines:
                chapter[line] = ''
        # for end of chapter, <hr used as an early cutoff
        end_of_chapter = chapter[-10:]
        line = find_line_of_value(end_of_chapter, '<hr')
        if line != -1:
            for i in range(line, 9):
                chapter[-1*i] = ''
    
    # recombine into a single string
    if len(chap_portions)+1 != len(chap_starts):  # valid values needed to update chap_starts
        raise Exception("chap_starts & chap_portions do not have valid values, len(chap_starts):"
                        + str(len(chap_starts)) + ", len(chap_portions)" + str(len(chap_portions)))
    string_portions = []
    chap_starts[0] = 0
    for index in range(len(chap_portions)):
        line_count = len(chap_portions[index])
        s = '\n'.join(chap_portions[index])
        string_portions.append(s)
        chap_starts[index+1] = chap_starts[index] + line_count
    full_text = '\n'.join(string_portions)

    section_indices = get_section_indices(chap_starts)

    book_dict = {"meta_values": meta_values,
                 "full_text": full_text,
                 "chapter_titles": chap_titles,
                 "chapter_divisions": chap_starts,
                 "section_indices": section_indices,
                 "meta_tags": meta_tags,
                 "pg_id": pg_id}
    return book_dict


def trim_chap_titles(chap_titles):
    # Trim undesired parts from chap_titles
    UNWANTED_IN_TITLE = "Chapter: "
    if chap_titles[0].startswith(UNWANTED_IN_TITLE) and not chap_titles[1].startswith(UNWANTED_IN_TITLE):
        chap_titles[0] = chap_titles[0][len(UNWANTED_IN_TITLE):]
    for i in range(len(chap_titles)):
        if chap_titles[i][-1] is ",":
            chap_titles[i] = chap_titles[i][:-1]


def get_meta_tags(sample, meta_portion):
    offset = len(sample)
    subject_lines = find_all_lines_of_value(meta_portion, sample)
    meta_tags = []
    for line in subject_lines:
        sample_position = meta_portion[line].find(sample)
        start_position = sample_position + offset
        end_position = meta_portion[line][start_position:].find('"') + start_position
        tag_string = meta_portion[line][start_position:end_position]
        tag_string = tag_string[:40]
        # cut off rest of subject tag string if the following are found
        cutoff_strings = [',', '(', '{', '[']
        tag_cutoff = tag_string.find(" --")
        for string in cutoff_strings:
            cur_cutoff = tag_string.find(string, 15)
            if cur_cutoff != -1 and (tag_cutoff == -1 or cur_cutoff < tag_cutoff):
                tag_cutoff = cur_cutoff
        if tag_cutoff == -1:
            meta_tags.append(tag_string)
        else:
            meta_tags.append(tag_string[:tag_cutoff])

    return meta_tags


def revise_toc_lines(toc_lines):
    avg_diff = (toc_lines[-1] - toc_lines[0]) / (0.0 + len(toc_lines))
    first_diff = toc_lines[1] - toc_lines[0]
    line_diff = abs(first_diff - avg_diff)
    if line_diff > first_diff / 4.0:  # denom might need to be much higher
        print("Unexpected line difference: " + str(line_diff) + " avg: " + str(avg_diff))
        old_sum = first_diff
        for i in range(2, len(toc_lines)):
            new_diff = toc_lines[i] - toc_lines[i - 1]
            new_sum = old_sum + new_diff
            old_avg_diff = old_sum / (i - 1)
            old_sum = new_sum
            # cutoff toc_lines at first big jump in lines relative to previous jumps
            if abs(old_avg_diff - new_diff) > old_avg_diff*1.5:
                print("old_diff: " + str(old_avg_diff) + " new_diff: " + str(new_diff))
                return toc_lines[:i]
    return toc_lines


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
    ch_id_index = 0
    for line_index in id_lines:
        cur_line = html_lines[line_index]
        cur_id = ch_ids[ch_id_index]
        if ('id="' + cur_id) in cur_line:
            ch_id_index += 1
            chap_starts.append(line_index)
            if ch_id_index == len(ch_ids):
                break
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
