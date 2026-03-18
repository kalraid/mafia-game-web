from __future__ import annotations

from collections import Counter
from typing import Dict, Optional, Tuple


def tally_votes(votes: Dict[str, str]) -> Tuple[Optional[str], bool]:
    """
    투표 집계.

    :param votes: voter_id -> target_player_id
    :return: (선정된 player_id 또는 None, 동률 여부)
    """
    if not votes:
        return None, False

    counter = Counter(votes.values())
    most_common = counter.most_common()

    if len(most_common) == 0:
        return None, False
    if len(most_common) == 1:
        return most_common[0][0], False

    top_count = most_common[0][1]
    tied = [player for player, count in most_common if count == top_count]
    if len(tied) > 1:
        return None, True

    return most_common[0][0], False
