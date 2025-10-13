import os
import openai

# Ensure you set OPENAI_API_KEY in your environment or Django settings
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_suggestions(metric_name: str, current_value: float, avg_value: float, trend: str) -> str:
    """
    Use OpenAI to generate actionable suggestions based on a metric.
    :param metric_name: Name of the metric (e.g. 'in_network_rate')
    :param current_value: Most recent value of the metric
    :param avg_value: Average value over the past year
    :param trend: One of 'increasing', 'decreasing', or 'flat'
    :return: Text with one or two suggestions
    """
    prompt = (
        f"The metric '{metric_name}' currently has a value of {current_value:.2f}, "
        f"with an average of {avg_value:.2f} over the past year. The trend is {trend}. "
        "Suggest one or two actionable improvements or interventions for reducing referral leakage."
    )
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.6,
    )
    return response.choices[0].text.strip()
