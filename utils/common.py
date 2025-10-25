

def limit(value, _min, _max):
    return max(min(value, _max), _min)


def print_progress_bar(iteration: int, total: int, label: str, bar_length: int = 30):
    """
    Prints a text-based progress bar to the console.
    
    :param iteration: Current iteration (int).
    :param total: Total iterations (int).
    :param bar_length: Length of the progress bar (int).
    :param label: label
    """
    percent = iteration / float(total) * 100
    filled_length = int(bar_length * iteration // total)
    bar = '#' * filled_length + '-' * (bar_length - filled_length)

    print(f'{label} {iteration:4d}/{total} |{bar}| {percent:.2f}%', end='\r')

    # Print New Line on Complete
    if iteration == total: 
        print()
