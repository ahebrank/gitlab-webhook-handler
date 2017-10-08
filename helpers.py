import re

class Helpers:

    def get_list_labels(self, boards):
        # return label IDs from all project boards
        label_ids = []
        for board in boards:
            label_ids += [list_label['label']['name'] for list_label in board['lists']]
        return label_ids

    def get_label_names(self, labels):
        return [label['name'] for label in labels]

    def get_issue_labels(self, issue):
        return issue['labels']

    def parse_commit_labels(self, message, labels):
        # get the issue numbers
        issue_pat = re.compile('#(\d+)')
        iid_match = issue_pat.findall(message)
        
        # get the labels
        label_pat = re.compile('([\~\+\-])(' + '|'.join(labels) + ')')
        label_match = label_pat.findall(message)
        return {
            'issues': iid_match,
            'label_ops': label_match
        }

    def simplify_labels(self, existing, from_message, board_labels = None):
        labels = existing
        for ops in from_message['label_ops']:
            op = ops[0]
            name = ops[1].decode('utf-8')
            if op == '+':
                labels.append(name)
            if op == '-':
                labels.remove(name)
            if op == '~':
                if name in board_labels:
                    # remove all board labels
                    labels = [label for label in labels if label not in board_labels]
                    # set board label
                    labels.append(name)
        return labels
