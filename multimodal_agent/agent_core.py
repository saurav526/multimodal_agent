from groq import Groq
class MultiModalAgent:
    """Sequential multi-agent orchestration using Groq chat completions."""

    def __init__(self, api_key: str, primary_model: str, reviewer_model: str):
        self.api_key = api_key
        self.client = Groq(api_key=api_key, timeout=90.0, max_retries=2)
        self.primary_model = primary_model
        self.reviewer_model = reviewer_model

    def complete(self, model: str, system: str, user: str, temperature: float = 0.25) -> str:
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_completion_tokens=4096,
        )
        return response.choices[0].message.content or ""

    def run(self, prompt: str, use_reviewer: bool = True) -> dict:
        plan = self.complete(
            self.primary_model,
            "You are the Planner agent. Break the request into practical steps, note assumptions, and identify the best response format. Do not fully answer yet.",
            prompt,
        )
        draft = self.complete(
            self.primary_model,
            "You are the Specialist agent. Answer the user's request accurately and usefully. For coding tasks, provide runnable code, explain files and commands, and flag assumptions.",
            f"User request:\n{prompt}\n\nPlanner notes:\n{plan}",
            0.35,
        )
        review = ""
        answer = draft
        if use_reviewer:
            review = self.complete(
                self.reviewer_model,
                "You are the Reviewer agent. Find errors, missing steps, unclear wording, or unsupported claims. Return concise actionable review notes.",
                f"User request:\n{prompt}\n\nDraft:\n{draft}",
                0.1,
            )
            answer = self.complete(
                self.primary_model,
                "You are the Finalizer agent. Write the final response, applying valid review notes. Do not reveal internal agent deliberation.",
                f"Request:\n{prompt}\n\nDraft:\n{draft}\n\nReview notes:\n{review}",
                0.2,
            )
        return {"plan": plan, "draft": draft, "review": review, "answer": answer}
