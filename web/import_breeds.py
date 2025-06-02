import csv
import os
import django
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "petmind.settings")
django.setup()

from dogs.models import DogBreed

def import_breeds():
    csv_path = os.path.join(BASE_DIR, 'data', '3_cleaned_dog_breeds.csv')
    
    if not os.path.exists(csv_path):
        return

    inserted = 0
    skipped = 0

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            breed_name = row.get('breed_name', '').strip()
            short_desc = row.get('short_description', '').strip()
            full_desc = row.get('full_description', '').strip()
            image_url = row.get('image_url', '').strip()

            if not breed_name:
                skipped += 1
                continue
            combined_description = f"{short_desc} {full_desc}".strip()

            try:
                obj, created = DogBreed.objects.get_or_create(
                    name=breed_name,
                    defaults={
                        'image_url': image_url,
                        'description': combined_description
                    }
                )
                if created:
                    inserted += 1
                else:
                    pass
            except Exception as e:
                skipped += 1

if __name__ == "__main__":
    import_breeds()
