class SearchFilter():
    def __init__(self, min_length=None, max_length=None, user_levels=None, decks=None):
        self.min_length = min_length
        self.max_length = max_length
        self.user_levels = user_levels
        self.decks = decks
        self.cur = None

    def has_filters(self):
        return self.min_length or self.max_length or self.user_levels or self.decks

    def get_min_length(self):
        return self.min_length

    def get_max_length(self):
        return self.max_length

    def set_cursor(self, cur):
        self.cur = cur

    def get_length_filter_string(self):
        if self.min_length and self.max_length:
            return "WHERE length(sentence) BETWEEN {} AND {}".format(self.min_length, self.max_length)
        elif self.min_length:
            return "WHERE length(sentence) >= {}".format(self.min_length)
        elif self.max_length:
            return "WHERE length(sentence) <= {}".format(self.max_length)
        else:
            return None

    def get_user_level_filter_string(self):
        if self.user_levels:
            if "JLPT" in self.user_levels and "WK" in self.user_levels:
                if self.user_levels["JLPT"] and self.user_levels["WK"]:
                    return "WHERE jlpt_level >= {} AND wk_level <= {}".format(self.user_levels['JLPT'], self.user_levels['WK'])
                elif self.user_levels["JLPT"]:
                    return "WHERE jlpt_level >= {}".format(self.user_levels['JLPT'])
                elif self.user_levels["WK"]:
                    return "WHERE wk_level <= {}".format(self.user_levels['WK'])
        return None

    def get_decks_filter_string(self):
        if self.decks:
            return "WHERE deck_name in {}".format(tuple(self.decks))
        else:
            return None 
    
    def get_query_string(self):
        if self.has_filters():
            filter_strings = [
                self.get_length_filter_string(),
                self.get_user_level_filter_string(),
                self.get_decks_filter_string()
            ]
            filter_condition = " AND ".join([s for s in filter_strings if s])
            return """SELECT id
                    FROM sentences
                    {}
                    """.format(filter_condition)
        else:
            return ""
