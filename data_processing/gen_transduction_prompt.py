from datasets import load_dataset
from datasets import Dataset
import json
from arc import validation_problems, train_problems


def parse_examples(text):
    # Split the text into training and test sections
    train_text, test_text = text.split("***Test example:***")

    # Parse training examples
    train_examples = []
    for example in train_text.split("[Example"):
        if "Input:" in example and "Output:" in example:
            input_text = example.split("Input:")[1].split("Output:")[0].strip().strip('`')
            output_text = example.split("Output:")[1].strip().strip("`")
            input_lines = [line.strip() for line in input_text.split("\n") if line.strip()]
            output_lines = [line.strip() for line in output_text.split("\n") if line.strip()]
            train_examples.append(("\n".join(input_lines), "\n".join(output_lines)))

    # Parse test example
    test_lines = [line.strip() for line in test_text.split("\n") if line.strip() and "output" not in line.lower() and 'Input' not in line]
    test_example = "\n".join(test_lines)

    return train_examples, [test_example]


# DEFAULT_SYSTEM_PROMPT = "You are an world-class puzzle solver who are extremely good at spotting patterns and solving puzzles. You are also an expert Python programmer who can write code to solve puzzles."
# DEFAULT_SYSTEM_PROMPT = "You are an world-class puzzle solver who are extremely good at spotting patterns and solving puzzles."
DEFAULT_SYSTEM_PROMPT = "You are a world-class puzzle solver with exceptional pattern recognition skills. Your task is to analyze puzzles, spot patterns, and provide direct solutions."
def convert_chat_format(question, answer):
    messages =  {
        "messages": [
            {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
    }
    if answer:
        messages["messages"].append({"role": "assistant", "content": answer})
    return messages

def make_problem_input_str(train_examples, test_examples):
    prompt ="Given input-output grid pairs as reference examples, carefully observe the patterns to predict the output grid for new test input. Each pair follows the same transformation rule. Grids are 2D arrays represented as strings, with cells (colors) separated by spaces and rows by newlines."
    prompt += "\nHere are the input and output grids for the reference examples:\n"
    for i, pair in enumerate(train_examples):
        prompt += f"Example {i+1}\n"
        prompt += f"Input:\n{pair[0]}\n\nOutput:\n{pair[1]}\n\n\n" 
    prompt += "Here is the input grid for the test example:\n"
    prompt += "Input:\n" + test_examples[0]
    prompt += "\n\nDirectly provide the output grids corresponding to the given test input grids, based on the patterns observed in the reference examples."
    return prompt

COLOR_MAPPING = {
0: "Black",
1: "Blue",
2: "Red",
3: "Green",
4: "Yellow",
5: "Gray",  # instead of "Grey"
6: "Pink",
7: "Orange",
8: "Purple",
9: "Brown"
}

def grid_to_str(grid):
    grid_str = ""
    for row in grid:
        row_str = ""
        for cell in row:
            row_str += f"{COLOR_MAPPING[cell]} "
        grid_str += row_str.strip() + "\n"
    return grid_str.strip()

def problem_grids_to_str(problem):
    train_examples_strs = []
    for train_pair in problem.train_pairs:
        train_x = grid_to_str(train_pair.x)
        train_y = grid_to_str(train_pair.y)
        train_examples_strs.append((train_x, train_y))
    test_examples_strs = []
    for test_pair in problem.test_pairs:
        test_x = grid_to_str(test_pair.x)
        test_examples_strs.append(test_x)
    
    return train_examples_strs, test_examples_strs
    

if __name__ == "__main__":


    
    PROBLEMS = validation_problems
    all_data = []
    for arc_problem in PROBLEMS:

        train_examples_strs, test_examples_strs = problem_grids_to_str(arc_problem)
        if len(test_examples_strs) > 1:
            print(arc_problem.uid)

        for i, test_examples_str in enumerate(test_examples_strs):
            question = make_problem_input_str(train_examples_strs, [test_examples_str])
            answer = f"The output grid for the test input grid is:\n\n```\n"
            
            all_data.append(convert_chat_format(question, answer))
            all_data[-1]["uid"] = arc_problem.uid
            all_data[-1]["answer"] = grid_to_str(arc_problem.test_pairs[i].y)


    print("==============input=============")
    print(all_data[0]["messages"][1]["content"])
    print("==============output=============")
    print(all_data[0]["messages"][2]["content"])
    print("==============answer=============")
    print(all_data[0]["answer"])

    print(f"Total number of examples: {len(all_data)}")


    # write to jsonl
    filename = "validation_transduction_prompt.jsonl"
    with open(filename, "w") as f:
        f.write("\n".join(json.dumps(p) for p in all_data))
    print(f"Saved to {filename}")
            
    # dataset_dict.push_to_hub("barc0/transduction_data", private=False)