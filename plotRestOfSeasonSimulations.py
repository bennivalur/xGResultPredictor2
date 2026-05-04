from datetime import date
import json

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def _lerp_color(start, end, t):
    return (
        int(start[0] + (end[0] - start[0]) * t),
        int(start[1] + (end[1] - start[1]) * t),
        int(start[2] + (end[2] - start[2]) * t),
    )


def _heat_color(percentage):
    if percentage <= 0:
        return (242, 246, 252)
    t = min(1.0, percentage / 35.0)
    low = (205, 227, 255)
    high = (24, 90, 189)
    return _lerp_color(low, high, t)


def _safe_team_label(team_name, max_chars=14):
    if len(team_name) <= max_chars:
        return team_name
    return team_name[: max_chars - 1] + "..."


def graphResultsOfSimulation(league, numberOfSimulations):
    with open("data/" + league + "/teamPositionsAtEndOfSeason.json", "r") as results:
        results = json.load(results)

    avg_position = {}
    for team in results:
        avg_pos = 0
        for position in results[team]:
            avg_pos += float(position) * float(results[team][position])
        avg_position[team] = avg_pos / numberOfSimulations

    avg_position = dict(sorted(avg_position.items(), key=lambda item: item[1]))
    sorted_teams = list(avg_position.keys())
    num_teams = len(sorted_teams)
    num_positions = len(next(iter(results.values())))

    cell_w = 96
    cell_h = 60
    left_margin = 275
    right_margin = 70
    top_margin = 265
    bottom_margin = 185
    width = left_margin + num_positions * cell_w + right_margin
    height = top_margin + num_teams * cell_h + bottom_margin

    im = Image.new("RGB", (width, height), (246, 249, 255))
    draw = ImageDraw.Draw(im)

    for y in range(height):
        blend = y / max(1, (height - 1))
        line_color = _lerp_color((247, 250, 255), (230, 238, 250), blend)
        draw.line((0, y, width, y), fill=line_color)

    title_font = ImageFont.truetype("fonts/Roboto-Black.ttf", 50)
    subtitle_font = ImageFont.truetype("fonts/Roboto-Light.ttf", 26)
    header_font = ImageFont.truetype("fonts/Roboto-Black.ttf", 28)
    team_font = ImageFont.truetype("fonts/Roboto-Black.ttf", 24)
    value_font = ImageFont.truetype("fonts/Roboto-Black.ttf", 24)
    footer_font = ImageFont.truetype("fonts/Roboto-Light.ttf", 24)

    title = "Rest Of Season Simulation - " + league.replace("_", " ")
    subtitle = "" + str(numberOfSimulations) + " simulation runs | each cell shows finish-position probability"
    draw.text((left_margin, 58), title, fill=(12, 32, 70), font=title_font)
    draw.text((left_margin, 116), subtitle, fill=(66, 87, 125), font=subtitle_font)

    # Place brand mark in the top-right corner without overpowering the chart.
    try:
        logo = Image.open("images/socksoverpants.png").convert("RGBA")
        max_logo_width = 118
        max_logo_height = 118
        scale = min(max_logo_width / logo.width, max_logo_height / logo.height, 1.0)
        resized_size = (max(1, int(logo.width * scale)), max(1, int(logo.height * scale)))
        logo = logo.resize(resized_size, Image.LANCZOS)

        logo_x = width - logo.width - 26
        logo_y = 22
        draw.rounded_rectangle(
            (logo_x - 10, logo_y - 10, logo_x + logo.width + 10, logo_y + logo.height + 10),
            radius=14,
            fill=(255, 255, 255),
            outline=(194, 208, 231),
            width=2,
        )
        im.paste(logo, (logo_x, logo_y), logo)
    except FileNotFoundError:
        pass

    grid_left = left_margin
    grid_top = top_margin
    grid_right = grid_left + num_positions * cell_w
    grid_bottom = grid_top + num_teams * cell_h

    draw.rounded_rectangle(
        (grid_left - 18, grid_top - 18, grid_right + 18, grid_bottom + 18),
        radius=22,
        fill=(255, 255, 255),
        outline=(178, 194, 221),
        width=3,
    )

    for row in range(num_teams):
        row_y0 = grid_top + row * cell_h
        row_y1 = row_y0 + cell_h
        if row % 2 == 1:
            draw.rectangle((grid_left, row_y0, grid_right, row_y1), fill=(249, 252, 255))

    for col in range(num_positions):
        x = grid_left + col * cell_w
        draw.line((x, grid_top, x, grid_bottom), fill=(224, 232, 245), width=1)
    draw.line((grid_right, grid_top, grid_right, grid_bottom), fill=(224, 232, 245), width=1)

    for row in range(num_teams + 1):
        y = grid_top + row * cell_h
        draw.line((grid_left, y, grid_right, y), fill=(224, 232, 245), width=1)

    for index in range(num_positions):
        pos_x = grid_left + index * cell_w + cell_w // 2
        draw.text((pos_x, grid_top - 46), str(index + 1), fill=(15, 40, 80), anchor="ms", font=header_font)

    draw.text((left_margin - 112, grid_top - 46), "Team", fill=(15, 40, 80), anchor="ms", font=header_font)

    for row, team in enumerate(sorted_teams):
        team_y = grid_top + row * cell_h + cell_h // 2
        draw.text((left_margin - 32, team_y), _safe_team_label(team), fill=(20, 44, 84), anchor="rm", font=team_font)

        for position, count in results[team].items():
            percentage = round(count / numberOfSimulations * 100, 1)
            col = int(position) - 1
            x0 = grid_left + col * cell_w + 6
            y0 = grid_top + row * cell_h + 6
            x1 = x0 + cell_w - 12
            y1 = y0 + cell_h - 12

            draw.rounded_rectangle(
                (x0, y0, x1, y1),
                radius=9,
                fill=_heat_color(percentage),
                outline=(177, 195, 223),
                width=1,
            )

            if percentage > 0:
                text_color = (255, 255, 255) if percentage >= 22 else (20, 46, 92)
                draw.text(
                    ((x0 + x1) // 2, (y0 + y1) // 2 + 1),
                    str(percentage) + "%",
                    fill=text_color,
                    anchor="mm",
                    font=value_font,
                )

    legend_top = grid_bottom + 56
    legend_left = grid_left
    legend_right = grid_left + min(560, num_positions * cell_w)
    legend_height = 24
    steps = max(1, legend_right - legend_left)

    for dx in range(steps):
        t = dx / max(1, steps - 1)
        pct = t * 35.0
        draw.line(
            (legend_left + dx, legend_top, legend_left + dx, legend_top + legend_height),
            fill=_heat_color(pct),
        )

    draw.rounded_rectangle(
        (legend_left, legend_top, legend_right, legend_top + legend_height),
        radius=6,
        outline=(170, 188, 215),
        width=1,
    )

    draw.text((legend_left, legend_top - 10), "0%", fill=(66, 87, 125), anchor="ls", font=subtitle_font)
    draw.text((legend_right, legend_top - 10), "35%+", fill=(66, 87, 125), anchor="rs", font=subtitle_font)

    today = date.today()
    footer = "Model and visual by @bennivaluR_ | " + str(today)
    draw.text((width // 2, height - 42), footer, fill=(72, 93, 130), anchor="ms", font=footer_font)
    draw.text((28, height - 42), "socksoverpants.com", fill=(72, 93, 130), anchor="ls", font=footer_font)

    #save image with unsharp mask to make it look better
    #have date in filename  to avoid caching issues when updating the image
    im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=140, threshold=2))
    im.save("images/simResults/" + league + "_resultsOfSeasonSimulation_" + str(today) + ".png", optimize=True)
