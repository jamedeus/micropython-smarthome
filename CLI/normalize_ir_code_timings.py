def normalize_timings(timings):
    '''Takes array of raw IR pulse/space integers (microseconds) recorded with
    lirc, returns array with timings normalized to NEC spec.

    Normalizing timings improves memory efficiency by reducing the number of
    ints that need to be allocated (recordings have random variance of a few
    microseconds that causes most ints to be unique, after normalizing there
    are only 4 ints).

    To record raw timings run `mode2 -d /dev/lirc0`, point remote at receiver,
    and press remote button. If you get hex codes instead of timings set
    `driver=default` in `/etc/lirc/lirc_options.conf`.
    '''
    normalized = []
    for t in timings:
        # Header pulse
        if 8500 <= t <= 9500:
            normalized.append(9000)
        # Header space
        elif 4000 <= t <= 5000:
            normalized.append(4500)
        # Logical 1 space
        elif 1500 <= t <= 1800:
            normalized.append(1690)
        # Logical 1 pulse, logical 0 space or pulse
        elif 500 <= t <= 700:
            normalized.append(560)
        # Add unexpected values unchanged
        else:
            normalized.append(t)
    return normalized
