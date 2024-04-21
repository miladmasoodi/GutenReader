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
    # return: dict of: meta_values, full_text, chap_titles, chap_starts, meta_tags
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
    meta_samples = [TITLE_SAMPLE, AUTHOR_SAMPLE, LANG_SAMPLE]
    meta_values = ["Title not found", "Unknown Author", "Language not found"]
    for index, sample in enumerate(meta_samples):
        sample_position = meta_portion.find(sample)
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
    toc_lines = find_all_lines_of_value(lines[:end_of_toc], 'href="#')

    # to see if it started counting non-toc <a>'s
    toc_lines = revise_toc_lines(toc_lines)

    chap_ids = find_id_values(lines, toc_lines)
    chap_starts = find_ch_start_lines(lines, chap_ids)
    chap_titles = find_chap_titles(lines, toc_lines)
    # print(chap_titles)
    # print(chap_ids)
    # print(chap_starts)
    if len(chap_ids) < len(chap_starts):
        raise Exception("too many chap_starts")

    chap_starts.append(end_line)
    print(meta_tags)

    book_dict = {"meta_values": meta_values, "full_text": '\n'.join(lines),
                 "chapter_titles": chap_titles, "chapter_divisions": chap_starts,
                 "meta_tags": meta_tags, "pg_id": pg_id}
    return book_dict


def get_meta_tags(sample, meta_portion):
    offset = len(sample)
    subject_lines = find_all_lines_of_value(meta_portion, sample)
    meta_tags = []
    for line in subject_lines:
        sample_position = meta_portion[line].find(sample)
        start_position = sample_position + offset
        end_position = meta_portion[line][start_position:].find('"') + start_position
        end = " -- "
        tag_string = meta_portion[line][start_position:end_position]
        tag_string = tag_string[:30]
        tag_cutoff = tag_string.find(end)
        if tag_cutoff != -1:
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
            if abs(old_avg_diff - new_diff) > old_avg_diff / 2.0:
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
