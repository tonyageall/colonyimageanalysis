from latch.resources.tasks import small_task
from latch.types.directory import LatchDir, LatchOutputDir
from latch.types.file import LatchFile
from pathlib import Path
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import ceil
import re
import os
import logging
from latch.functions.operators import List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@small_task
def task(
    JpgFiles: List[LatchFile],
    output_directory: LatchOutputDir
) -> LatchDir:
    temp_dir = Path("/root/latch_temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    def image_df(jpg, contrastL, contrastR):
        image = cv2.imread(jpg, cv2.IMREAD_GRAYSCALE)
        _, thresh = cv2.threshold(image, contrastL, contrastR, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bright_spots = []
        for cnt in contours:
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                bright_spots.append((cX, cY))
        
        rows, cols = 16, 24
        plate_width, plate_height = image.shape[1], image.shape[0]
        well_width, well_height = plate_width / cols, plate_height / rows
        row_labels = [chr(i) for i in range(65, 65 + rows)]
        
        well_positions = []
        for (cX, cY) in bright_spots:
            col = int(cX / well_width) + 1
            row = int(cY / well_height)
            well_positions.append((row_labels[row], col))
        df = pd.DataFrame(well_positions, columns=['Row', 'Column'])
        
        return df

    data_frames = []
    for file in JpgFiles:
        logging.info(f"Processing file: {file}")
        plate = re.search(r'384WP[0-9]{0,4}', file.local_path)
        if plate:
            ID = plate.group()
            DF = image_df(file.local_path, 100, 255)
            DF['Source_place'] = ID
            DF['Source_Well'] = DF.apply(lambda row: f"{row['Row']}{str(row['Column']).zfill(2)}", axis=1)
            data_frames.append(DF)
        else:
            logging.warning(f"Plate ID not found in file name: {file.local_path}")

    if data_frames:
        DATA = pd.concat(data_frames)
    else:
        logging.error("No data frames to concatenate. Exiting.")
        return LatchDir(output_directory.remote_path)

    def plates(x, y, target_max):
        quotient = ceil(x / y)
        return min(quotient, target_max)

    max_colonies_per_plate = 96
    num_colony_wells = len(DATA)
    num_plates_needed = plates(num_colony_wells, max_colonies_per_plate, 8)
    
    ROWS = list("ABCDEFGH")
    COLUMNS = [f"{i:02}" for i in range(1, 13)]
    total_wells = len(ROWS) * len(COLUMNS)
    num_repetitions = ceil(num_colony_wells / total_wells)
    WELLS = [f"{row}{col}" for row in ROWS for col in COLUMNS] * num_repetitions
    
    CHERRY = []
    for plate_num in range(1, num_plates_needed + 1):
        start_row = (plate_num - 1) * max_colonies_per_plate
        end_row = min(num_colony_wells, start_row + max_colonies_per_plate)
        plate_data = DATA.iloc[start_row:end_row].copy()
        plate_data['Destination_Plate'] = f"DEST[{plate_num}]"
        plate_data['Destination_Well'] = WELLS[start_row:end_row]
        CHERRY.append(plate_data)

    CHERRY_df = pd.concat(CHERRY)
    output_csv_path = temp_dir / 'CherryPick.csv'
    CHERRY_df.to_csv(output_csv_path, index=False)
    logging.info(f"Saved combined data to {output_csv_path}")

    for file in JpgFiles:
        logging.info(f"Annotating and saving image for file: {file}")
        plate = re.search(r'384WP[0-9]{0,4}', file.local_path)
        if plate:
            ID = plate.group()
            image_path = file.local_path
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            _, thresh = cv2.threshold(image, 100, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            bright_spots = []
            for cnt in contours:
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    bright_spots.append((cX, cY))

            rows, cols = 16, 24
            plate_width, plate_height = image.shape[1], image.shape[0]
            well_width, well_height = plate_width / cols, plate_height / rows
            row_labels = [chr(i) for i in range(65, 65 + rows)]

            well_positions = []
            for (cX, cY) in bright_spots:
                col = int(cX / well_width) + 1
                row = int(cY / well_height)
                well_positions.append((row_labels[row], col))
                label = f"{row_labels[row]}{col}"
                cv2.circle(image, (cX, cY), 5, (255, 255, 255), -1)
                cv2.putText(image, label, (cX - 10, cY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)

            annotated_image_path = temp_dir / f"{ID}.jpg"
            cv2.imwrite(str(annotated_image_path), image)
            logging.info(f"Saved annotated image to {annotated_image_path}")
        else:
            logging.warning(f"Plate ID not found in file name: {file.local_path}")

    logging.info("Uploading results")
    return LatchOutputDir(str(temp_dir), output_directory.remote_path)
