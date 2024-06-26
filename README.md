# RCTool
RCTool consists of two components, i.e., a modeler and an analyzer.
1) The modeler is implemented on the open-source Petri tool PIPE (https://sarahtattersall.github.io/PIPE/) , which can help emergency organizations visually model their response processes. The output of the modeler is a PNML file extended with initial markings, final markings, message places, labels, resource places, and uncertain firing delays. The following figure shows the emergency response processes in our motiving example FMR (accessed at: https://github.com/MoqiYNU/RCTool/blob/main/Motivating%20Example.xml) modeled by the modeler.

![截屏](https://github.com/MoqiYNU/RCTool/assets/49392929/26ba4304-7952-4ef8-9748-2a495d5956f7)


2) The analyzer takes as input the PNML file generated by the modeler, and then automatically constructs a resolved CERP. The following figure shows the resolved CERP of FMR built by the analyzer, which is described by the tool Graphviz (https://www.graphviz.org/).

![optimizde CERP](https://github.com/MoqiYNU/RCTool/assets/49392929/b7776b66-136b-494a-9699-67a3f0ce30b4)

 


