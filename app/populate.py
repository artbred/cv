import argparse

from labels import Label, calculate_embedding, get_most_similar_label
from settings import create_id, min_similarity_score
from storage import create_redis_connection, init_index, labels_prefix_key

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--flush", action="store_true", help="Clear redis and initialize new schema")
args = parser.parse_args()

if args.flush:
    init_index()


position_labels = [
    Label(
        id=create_id(prefix=labels_prefix_key),
        position="product manager",
        path_to_file="../data/resumes/ArtemProductV1.pdf",
        from_redis=False,
    ),
    Label(
        id=create_id(prefix=labels_prefix_key),
        position="backend developer",
        path_to_file="../data/resumes/ArtemBackendV1.pdf",
        from_redis=False,
    ),
]


with create_redis_connection() as conn:
    # Delete labels
    keys = conn.keys(f"{labels_prefix_key}*")
    if keys:
        conn.delete(*keys)

    # Save new labels to redis
    for label in position_labels:
        label.save_to_redis()

    # Test if redis search works
    index_test_label = 0

    test_ok_label = position_labels[index_test_label]
    test_ok_embedding = calculate_embedding(test_ok_label.position)

    most_similar_label, score = get_most_similar_label(test_ok_embedding)
    print(f"Score for correct label: {score}")
    assert score > min_similarity_score

    test_false_text = "cdjsbcsdiuvbniuverger"
    test_false_embedding = calculate_embedding(test_false_text)

    most_similar_label, score = get_most_similar_label(test_false_embedding)
    print(f"Score for incorrect label: {score}")
    assert score < min_similarity_score
