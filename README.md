# RCTool
RCTool consists of two components, i.e., a modeler and an analyzer.
1) The modeler is implemented on the open-source Petri tool PIPE (Platform Independent Petri net Editor) , which can help emergency organizations visually model their response processes. The output of the modeler is a PNML file extended with initial markings, final markings, message places, labels, resource places, and uncertain firing delays. The following figure shows the emergency response processes in our motiving example FMR modeled by the modeler.

<img width="204" alt="image" src="https://github.com/MoqiYNU/RCTool/assets/49392929/fdee9c9a-adc3-461e-83e2-826805ac01a5">

2) The analyzer takes as input the PNML file generated by the modeler, and then automatically constructs a resolved CERP. The following figure shows the resolved CERP of FMR built by the analyzer, which is described by the tool Graphviz .![image](https://github.com/MoqiYNU/RCTool/assets/49392929/6891dfef-3d8c-4aeb-a858-0fb55f65d7ec)


