class SearchOrder():
    def __init__(self, sorting=None):
        self.sorting = sorting

    def has_order(self):
        if self.sorting:
            return self.sorting.lower() in ['sentence length', 'shortness', 'longness']
        else:
            return False

    def get_order(self):
        if self.has_order():
            if self.sorting.lower() in ['sentence length', 'shortness']:
                return "ORDER BY length(sentence)"
            elif self.sorting.lower() == 'longness':
                return "ORDER BY length(sentence) DESC"
        else:
            return ""