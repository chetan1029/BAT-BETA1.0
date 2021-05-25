def get_visibility_score(frequency, rank, page):
    """Calculate Visibility Score for the keyword."""
    visibility_score = 0
    # Our formula /1000 give negative value of 1m plus rank so limit the rank
    if frequency > 1000000:
        frequency = 999999
    keyword_quantity_score = round(((1000 - (frequency / 1000)) / 10), 1)
    if page == 1 and rank <= 3:
        search_share = 42
    elif page == 1 and rank >= 4 and rank <= 16:
        search_share = 38
    elif page == 2:
        search_share = 16
    elif page == 3:
        search_share = 4
    else:
        search_share = 0
    if search_share:
        visibility_score = round(
            (keyword_quantity_score * search_share) / 100, 2
        )
    return visibility_score
