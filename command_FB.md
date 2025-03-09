Generate requierment.txt using pipreqs --force --ignore .venv --mode no-pin
pip install -r ./requirements.txt
<!-- bash -->
find ./data/cards_image_gallery -type f -iname \*.jpg -delete
find ./data/bad_image -type f -iname \*.jpg -delete

<!-- python  -->
from collections import Counter
set_type_counts = Counter(card.set_type for card in cards.values())