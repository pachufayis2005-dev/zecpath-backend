class ScoringEngine:
    """
    Evaluates interview answers.
    """

    KEYWORDS = {
        "django": [
            "django",
            "orm",
            "model",
            "view",
            "serializer",
            "rest",
            "migration",
        ],
        "python": [
            "python",
            "oop",
            "class",
            "function",
            "decorator",
            "list",
            "tuple",
        ],
    }

    def keyword_score(self, answer, job_title):

        answer = answer.lower()
        job_title = job_title.lower()

        keywords = []

        if "django" in job_title:
            keywords = self.KEYWORDS["django"]

        elif "python" in job_title:
            keywords = self.KEYWORDS["python"]

        matched = []

        for keyword in keywords:

            if keyword in answer:
                matched.append(keyword)

        if not keywords:
            return 100, matched

        score = (len(matched) / len(keywords)) * 100

        return round(score, 2), matched

    def completeness_score(self, answer):

        words = len(answer.split())

        if words >= 50:
            return 100

        if words >= 30:
            return 80

        if words >= 15:
            return 60

        return 30

    def confidence_score(self, answer):

        answer = answer.lower()

        weak_words = [
            "maybe",
            "probably",
            "i think",
            "not sure",
        ]

        penalty = 0

        for word in weak_words:

            if word in answer:
                penalty += 15

        score = max(100 - penalty, 40)

        return score

    def final_score(
        self,
        relevance,
        completeness,
        confidence,
    ):

        return round(
            (relevance * 0.5 + completeness * 0.3 + confidence * 0.2),
            2,
        )
