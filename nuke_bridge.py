#!/usr/bin/env python
    import sys
    import json
    import traceback

    # Function to handle response formatting
    def respond(success=True, data=None, error=None):
        response = {
            "success": success,
            "data": data
        }
        if error:
            response["error"] = error
        print(json.dumps(response))

    # Main function to process commands
    def main():
        if len(sys.argv) < 2:
            respond(False, None, "No command specified")
            return

        command = sys.argv[1]
        args = {}
        
        # Parse arguments if provided
        if len(sys.argv) > 2:
            try:
                args = json.loads(sys.argv[2])
            except json.JSONDecodeError as e:
                respond(False, None, f"Invalid JSON arguments: {str(e)}")
                return

        try:
            # Import nuke here to avoid errors when running outside of Nuke
            try:
                import nuke
            except ImportError:
                respond(False, None, "Failed to import nuke module. Make sure this script is run within Nuke.")
                return

            # Process the command
            if command == "createNode":
                create_node(args, nuke)
            elif command == "setKnobValue":
                set_knob_value(args, nuke)
            elif command == "getNode":
                get_node(args, nuke)
            elif command == "execute":
                execute(args, nuke)
            else:
                respond(False, None, f"Unknown command: {command}")
        except Exception as e:
            respond(False, None, f"Error executing command: {str(e)}\n{traceback.format_exc()}")

    # Command implementations
    def create_node(args, nuke):
        if "nodeType" not in args:
            respond(False, None, "nodeType parameter is required")
            return
            
        node_type = args["nodeType"]
        name = args.get("name")
        inputs = args.get("inputs", [])
        
        try:
            # Create the node
            node = nuke.createNode(node_type, inpanel=False)
            
            # Set name if provided
            if name:
                node["name"].setValue(name)
                
            # Connect inputs if provided
            for i, input_name in enumerate(inputs):
                input_node = nuke.toNode(input_name)
                if input_node:
                    node.setInput(i, input_node)
                else:
                    respond(False, None, f"Input node not found: {input_name}")
                    return
            
            # Return node info
            node_info = {
                "name": node.name(),
                "type": node.Class(),
                "position": {"x": node.xpos(), "y": node.ypos()}
            }
            respond(True, node_info)
        except Exception as e:
            respond(False, None, f"Error creating node: {str(e)}")

    def set_knob_value(args, nuke):
        if "nodeName" not in args:
            respond(False, None, "nodeName parameter is required")
            return
        if "knobName" not in args:
            respond(False, None, "knobName parameter is required")
            return
        if "value" not in args:
            respond(False, None, "value parameter is required")
            return
            
        node_name = args["nodeName"]
        knob_name = args["knobName"]
        value = args["value"]
        
        try:
            node = nuke.toNode(node_name)
            if not node:
                respond(False, None, f"Node not found: {node_name}")
                return
                
            if knob_name not in node.knobs():
                respond(False, None, f"Knob not found: {knob_name}")
                return
                
            node[knob_name].setValue(value)
            
            respond(True, {
                "node": node_name,
                "knob": knob_name,
                "value": value
            })
        except Exception as e:
            respond(False, None, f"Error setting knob value: {str(e)}")

    def get_node(args, nuke):
        if "nodeName" not in args:
            respond(False, None, "nodeName parameter is required")
            return
            
        node_name = args["nodeName"]
        
        try:
            node = nuke.toNode(node_name)
            if not node:
                respond(False, None, f"Node not found: {node_name}")
                return
                
            # Collect basic node info
            node_info = {
                "name": node.name(),
                "type": node.Class(),
                "position": {"x": node.xpos(), "y": node.ypos()},
                "knobs": {}
            }
            
            # Collect knob values (only for basic types that can be serialized)
            for knob in node.knobs():
                try:
                    k = node[knob]
                    # Handle different knob types
                    if k.Class() in ["String_Knob", "File_Knob", "Text_Knob"]:
                        node_info["knobs"][knob] = k.value()
                    elif k.Class() in ["Int_Knob", "Double_Knob", "Boolean_Knob", "XY_Knob"]:
                        node_info["knobs"][knob] = k.value()
                    # Skip complex knobs that can't be easily serialized
                except:
                    pass
                    
            respond(True, node_info)
        except Exception as e:
            respond(False, None, f"Error getting node info: {str(e)}")

    def execute(args, nuke):
        if "writeNodeName" not in args:
            respond(False, None, "writeNodeName parameter is required")
            return
        if "frameRangeStart" not in args:
            respond(False, None, "frameRangeStart parameter is required")
            return
        if "frameRangeEnd" not in args:
            respond(False, None, "frameRangeEnd parameter is required")
            return
            
        write_node_name = args["writeNodeName"]
        frame_start = args["frameRangeStart"]
        frame_end = args["frameRangeEnd"]
        
        try:
            write_node = nuke.toNode(write_node_name)
            if not write_node:
                respond(False, None, f"Write node not found: {write_node_name}")
                return
                
            if write_node.Class() != "Write":
                respond(False, None, f"Node {write_node_name} is not a Write node")
                return
                
            # Execute the write node
            nuke.execute(write_node, int(frame_start), int(frame_end))
            
            respond(True, {
                "node": write_node_name,
                "rendered": True,
                "frameRange": {"start": frame_start, "end": frame_end},
                "outputPath": write_node["file"].value()
            })
        except Exception as e:
            respond(False, None, f"Error executing write node: {str(e)}")

    if __name__ == "__main__":
        main()
