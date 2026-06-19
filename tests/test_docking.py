from pathlib import Path

from bindtox.docking import extract_scores


def test_extract_scores_accepts_integer_rmsd_values(tmp_path: Path):
    log_path = tmp_path / "vina.log"
    log_path.write_text(
        """
mode |   affinity | dist from best mode
     | (kcal/mol) | rmsd l.b.| rmsd u.b.
-----+------------+----------+----------
   1        -10.9          0          0
   2         -8.4      1.250      2.500
""",
        encoding="utf-8",
    )

    assert extract_scores(log_path) == [
        {"mode": 1, "energy": -10.9, "rmsd_lb": 0.0, "rmsd_ub": 0.0},
        {"mode": 2, "energy": -8.4, "rmsd_lb": 1.25, "rmsd_ub": 2.5},
    ]
