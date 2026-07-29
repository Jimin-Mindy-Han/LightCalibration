import script_to_lighting_temperature
import UE_remote_control_dmx as control_dmx

def main():
    output = ask_llm.output_lighting_option("scripts/2.txt")
    print(output)
    temperature = output["lighting_temperature"]
    print("temperature: ", temperature)
    control_dmx.dmx_remote_control(temperature)

if __name__=="__main__":
    main()