import pandas as pd
from typing import List, Dict
from dataclasses import dataclass, field
from pathlib import Path
import time

@dataclass
class EvalCase:
    id: int
    title: str
    type: str
    demo: bool
    input: str
    ground_truth: List[str]

@dataclass
class EvalRun:
    """Stores evaluation results and calculates metrics for an evaluation run."""
    results: Dict[int, dict]
    timestamp: float = field(default_factory=time.time)

    @property
    def total_cases(self) -> int:
        """Total number of evaluation cases."""
        return len(self.results)
    
    @property
    def passed_cases(self) -> int:
        """Number of passing evaluation cases."""
        return sum(1 for result in self.results.values() if result['passed'])
    
    @property
    def pass_rate(self) -> float:
        """Percentage of passing cases."""
        return (self.passed_cases / self.total_cases) * 100 if self.total_cases > 0 else 0
    
    def get_failed_cases(self) -> List[int]:
        """Returns list of case IDs that failed."""
        return [case_id for case_id, result in self.results.items() if not result['passed']]
    
    def summary(self) -> str:
        """Returns a formatted summary of the evaluation results."""
        summary_lines = [
            f"Evaluation Summary:",
            f"Total cases: {self.total_cases}",
            f"Passed cases: {self.passed_cases}",
            f"Pass rate: {self.pass_rate:.1f}%"
        ]
        return "\n".join(summary_lines)


def load_eval_cases(csv_path: str | Path) -> List[EvalCase]:
    """
    Load evaluation cases from a CSV file into a list of EvalCase objects.
    
    Args:
        csv_path: Path to the evals CSV file
        
    Returns:
        List of EvalCase objects containing the parsed data
    """
    df = pd.read_csv(csv_path)
    
    eval_cases = []
    for _, row in df.iterrows():
        
        if row['type'] == 'patent':
            # Convert string representation of list to actual list based on type
            ground_truth_str = row['ground_truth'].strip('[]')

            # For patent type, split by comma and ensure clean patent IDs
            ground_truth = [x.strip().upper() for x in ground_truth_str.split(',') if x.strip()]
        else:
            raise ValueError(f"Unsupported evaluation case type: {row['type']}")
        
        case = EvalCase(
            id=row['id'],
            title=row['title'],
            type=row['type'],
            demo=row['demo'],
            input=row['input'],
            ground_truth=ground_truth
        )
        eval_cases.append(case)
    
    return eval_cases

def dummy_process_input(input_text: str, case_type: str) -> List[str]:
    """
    Placeholder function that simulates processing input text.
    In practice, this would be replaced with your actual processing logic.
    
    Args:
        input_text: The input text to process
        case_type: The type of case being processed (e.g. 'patent')
        
    Returns:
        List of processed strings
        
    Raises:
        ValueError: If case_type is not recognized
    """
    if case_type == 'patent':
        # For patent type, return 5 random numbers as strings
        import random
        return [str(random.randint(0, 9000000)) for _ in range(5)]
    
    raise ValueError(f"Unsupported case type: {case_type}")

def run_and_evaluate(eval_cases: List[EvalCase]) -> EvalRun:
    """
    Run evaluation cases through the processing function and compare with expected output.
    
    Args:
        eval_cases: List of EvalCase objects to evaluate
        
    Returns:
        EvalRun object containing evaluation results and metrics
    """
    results = {}
    
    for case in eval_cases:
        # Run the input through processing
        predicted_output = dummy_process_input(case.input, case.type)

        # TODO parse the predicted output depending on case type
        
        # Initialize result dictionary
        result = {
            'title': case.title,
            'type': case.type,
            'expected': case.ground_truth,
            'predicted': predicted_output,
            'passed': False
        }
        
        # Evaluate based on case type
        if case.type == 'patent':
            # Assert that predicted_output is a list
            assert isinstance(predicted_output, list), f"Predicted output must be a list, got {type(predicted_output)}"
            
            # Check if all ground truth patents are in predicted output (order doesn't matter)
            result['passed'] = all(gt_patent in predicted_output for gt_patent in case.ground_truth)
        else:
            raise ValueError(f"Unknown evaluation case type: {case.type}")
            
        results[case.id] = result
    
    return EvalRun(results=results)

# Example usage
if __name__ == "__main__":
    eval_cases = load_eval_cases('eval/generated_evals.csv')
    # eval_cases = load_eval_cases('eval/demo_evals.csv')
    eval_run = run_and_evaluate(eval_cases)
    
    # Print summary
    print(eval_run.summary())
    
    # Print detailed results if needed
    for case_id in eval_run.get_failed_cases():
        result = eval_run.results[case_id]
        print(f"\nFailed Case {case_id}: {result['title']}")
        print(f"Expected: {result['expected']}")
        print(f"Predicted: {result['predicted']}")
