import itertools as it
import re

class FormatReport:
    def __init__(self):
        self.headers = ['#', 'Type', 'Comment', 'Segment', 'Row-col #', 'Expected', 'Got', 'Mark']
        self.values = []
        self.get_table_data()
    def get_table_data(self):
        default = ['','','','','','','','Unknown']
        table = []
        with open('sparse/report/sparse_report.txt') as f:
            file_pos = 0
            regex_str = '.*warning: incorrect type in argument \d+ \(different address spaces\)$'
            for read_data in f:
                file_pos += len(read_data)
                result = re.match(regex_str,read_data)
                if result:
                    table.append([_ for _ in default])
                    curr_index = len(table) - 1
                    table[curr_index][0] = curr_index + 1
                    table[curr_index][1] = 'Warning'
                    segment, table[curr_index][2] = read_data.split(": warning: ")
                    table[curr_index][3], table[curr_index][4] = segment.split(":",1)
                    expected_data = f.readline()
                    z = re.match('.*: *expected.*$',expected_data)
                    if z == None:
                        f.seek(file_pos)
                        continue
                    file_pos += len(expected_data)
                    temp, table[curr_index][5] = re.split(":[ ]*expected ", expected_data)
                    got_data = f.readline()
                    file_pos += len(got_data)
                    temp, table[curr_index][6] = re.split(":[ ]*got ",got_data)
        self.values = table
