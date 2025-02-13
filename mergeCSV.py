import csv
import os

# Directory containing CSV files
directory = "NBAdata14_24"

# Output CSV file name
output_file = "output.csv"

# List to store second row data from each file
second_row_data = []

# Iterate through each file in the directory
for filename in os.listdir(directory):
    if filename.endswith(".csv"):
        with open(os.path.join(directory, filename), 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            # Skip the first row
            next(csv_reader)
            # Read the second row and append to second_row_data list
            second_row = next(csv_reader, None)
            if second_row:
                second_row_data.append(second_row)

# Write the second row data to a new CSV file
with open(output_file, 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerows(second_row_data)

print("Second row data from each file has been written to", output_file)
