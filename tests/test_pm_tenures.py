from hansard_pm_extraction.pm_tenures import _prime_minister_posts


def test_prime_minister_posts_matches_plain_title():
    posts = [{"name": "Prime Minister", "startDate": "2019-07-24", "endDate": "2022-09-06"}]
    assert _prime_minister_posts(posts) == posts


def test_prime_minister_posts_matches_compound_title():
    posts = [
        {
            "name": "Prime Minister, First Lord of the Treasury, "
            "Minister for the Civil Service, and Minister for the Union",
            "startDate": "2022-10-25",
            "endDate": "2024-07-05",
        }
    ]
    assert _prime_minister_posts(posts) == posts


def test_prime_minister_posts_excludes_unrelated_posts():
    posts = [
        {"name": "Chancellor of the Exchequer", "startDate": "2020-02-13", "endDate": "2022-07-05"},
        {
            "name": "Parliamentary Under-Secretary to the Prime Minister",
            "startDate": "2018-01-01",
            "endDate": "2019-01-01",
        },
    ]
    assert _prime_minister_posts(posts) == []


def test_prime_minister_posts_empty_input():
    assert _prime_minister_posts([]) == []
