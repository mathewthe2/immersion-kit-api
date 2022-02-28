class SearchFilter():
    def __init__(self, min_length=None, max_length=None):
        self.min_length = min_length
        self.max_length = max_length
        self.cur = None

    def has_filters(self):
        return self.min_length or self.max_length

    def get_min_length(self):
        return self.min_length

    def get_max_length(self):
        return self.max_length

    def set_cursor(self, cur):
        self.cur = cur

    def get_length_filter_string(self):
        if self.min_length and self.max_length:
            return "WHERE length(sentence) BETWEEN {} and {}".format(self.min_length, self.max_length)
        elif self.min_length:
            return "WHERE length(sentence) >= {}".format(self.min_length)
        elif self.max_length:
            return "WHERE length(sentence) <= {}".format(self.max_length)
        else:
            return None

    def get_query_string(self):
        if self.has_filters():
            filter_condition = " AND ".join([s for s in [self.get_length_filter_string()] if s])
            return """SELECT id
                    FROM sentences
                    {}
                    """.format(filter_condition)
        else:
            return ""
