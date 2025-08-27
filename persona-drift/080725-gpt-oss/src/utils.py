import torch

class GPTOSSChat:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.conversation = []
    
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def add_turn(self, user_input):
        """Add a user turn and get model response"""
        self.conversation.append({"role": "user", "content": user_input})
        
        inputs = self.tokenizer.apply_chat_template(
            self.conversation, 
            add_generation_prompt=True, 
            return_tensors="pt",
            return_dict=True
        )
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens = 2000,
                pad_token_id = self.tokenizer.eos_token_id,
                do_sample = False
            )
        
        input_length = inputs["input_ids"].shape[-1]
        full_response = self.tokenizer.decode(output[0, input_length:])
        # final_response = self._extract_final_response(full_response)
        
        self.conversation.append({"role": "assistant", "content": full_response})
        return full_response
    
    def chat(self, user_input):
        """Simple chat - returns only the final response"""
        full_response = self.add_turn(user_input)
        return self._extract_final_response(full_response)
    
    def _extract_final_response(self, harmony_output):
        """Extract the final channel content from harmony format"""
        if "<|channel|>final<|message|>" in harmony_output:
            start = harmony_output.find("<|channel|>final<|message|>") + len("<|channel|>final<|message|>")
            end = harmony_output.find("<|", start)
            if end == -1:
                return harmony_output[start:].strip()
            return harmony_output[start:end].strip()
        return harmony_output
    
    def reset(self):
        """Clear conversation history"""
        self.conversation = []
        return "Conversation reset!"
    
    def get_history(self):
        """Get current conversation"""
        return self.conversation.copy()
    
    def show_conversation(self):
        """Print the current conversation"""
        for i, msg in enumerate(self.conversation):
            role = msg['role'].capitalize()
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"{i+1}. {role}: {content}")
    
    def save_conversation(self, filename):
        """Save conversation to file"""
        import json
        with open(filename, 'w') as f:
            json.dump(self.conversation, f, indent=2)
        print(f"Conversation saved to {filename}")
    
    def load_conversation(self, filename):
        """Load conversation from file"""
        import json
        with open(filename, 'r') as f:
            self.conversation = json.load(f)
        print(f"Conversation loaded from {filename}")

    def get_reasoning(self, turn_number=None):
        """Extract reasoning from any turn. If turn_number is None, gets last turn."""
        if turn_number is None:
            for i in range(len(self.conversation) - 1, -1, -1):
                if self.conversation[i]["role"] == "assistant":
                    full_response = self.conversation[i]["content"]
                    break
            else:
                return "No assistant responses found"
        else:
            assistant_index = (turn_number * 2) - 1
            if assistant_index >= len(self.conversation) or self.conversation[assistant_index]["role"] != "assistant":
                return f"Turn {turn_number} not found"
            full_response = self.conversation[assistant_index]["content"]

        if "<|channel|>analysis<|message|>" in full_response:
            start = full_response.find("<|channel|>analysis<|message|>") + len("<|channel|>analysis<|message|>")
            end = full_response.find("<|end|>", start)
            if end == -1:
                next_channel = full_response.find("<|start|>assistant<|channel|>", start)
                end = next_channel if next_channel != -1 else len(full_response)
            return full_response[start:end].strip()
        return "No reasoning found in this response"