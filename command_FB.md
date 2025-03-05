Generate requierment.txt using pipreqs --force --ignore .venv --mode no-pin
pip install -r ./requirements.txt
<!-- bash -->
find . -type f -iname \*.jpg -delete


<!-- python  -->
from collections import Counter
set_type_counts = Counter(card.set_type for card in cards.values())