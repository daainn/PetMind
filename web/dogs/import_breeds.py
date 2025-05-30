# dogs/import_breeds.py

import csv
from dogs.models import DogBreed

def import_breeds():
    with open('data/3_cleaned_dog_breeds.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            short_desc = row.get('short_description', '')
            full_desc = row.get('full_description', '')
            combined_description = f"{short_desc} {full_desc}".strip()

            DogBreed.objects.get_or_create(
                name=row['breed_name'],  # breed_name → name
                defaults={
                    'image_url': row.get('image_url', ''),
                    'description': combined_description  # characteristic → description
                }
            )
