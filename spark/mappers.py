

#coursera example
def split_show_views(line):
    show = line.split(",")[0]
    views = int(line.split(",")[1])
    return (show, views)

#coursera example
def split_show_channel(line):
    show = line.split(",")[0]
    channel = line.split(",")[1]
    return (show, channel)

#coursera example
def extract_channel_views(show_views_channel): 
    views_channel = show_views_channel[1]
    views = views_channel[0]
    channel = views_channel[1]
    return (channel, views)