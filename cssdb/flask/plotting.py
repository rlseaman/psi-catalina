import io

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


def generate_coordinate_scatter_plot(coordinates, main_label, detail_label):
    ras = [coordinate[0] for coordinate in coordinates]
    decs = [coordinate[1] for coordinate in coordinates]
    fig = Figure(figsize=(10, 5))

    summary = fig.add_subplot(1, 2, 1)
    summary.set_xlabel("Right Ascension (degrees)")
    summary.set_ylabel("Declination (degrees)")
    summary.set_title(main_label)
    summary.set_xlim(0, 360)
    summary.set_ylim(-90, 90)
    summary.scatter(ras, decs, s=3, color='blue', alpha=0.5)

    detail = fig.add_subplot(1, 2, 2)
    detail.set_xlabel("Right Ascension (degrees)")
    detail.set_ylabel("Declination (degrees)")
    detail.set_title(detail_label)
    detail.scatter(ras, decs, s=3, color='blue', alpha=0.5)

    b = io.BytesIO()
    FigureCanvas(fig).print_png(b)
    return b


def parse_triplet(val):
    hd, m, s = split_triplet(val)
    return int(hd), int(m), float(s)


def split_triplet(val):
    return val.split(":") if ":" in val else val.split(" ")


def ra_hms_to_dec(hours, minutes, seconds):
    # return (hours/24.0*360.0) + (minutes/24.0/60.0*360.0) + (seconds/24.0/60.0/60.0*360.0)
    return hours * 15.0 + minutes / 4.0 + seconds / 240.0


def dec_dms_to_dec(degrees, minutes, seconds):
    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def convert_ra_decs(values):
    return [(ra_hms_to_dec(*parse_triplet(ra)), dec_dms_to_dec(*parse_triplet(dec))) for (ra, dec) in values if
            ra and dec]
