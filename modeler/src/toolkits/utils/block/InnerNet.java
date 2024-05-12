package toolkits.utils.block;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import toolkits.def.petri.Flow;
import toolkits.utils.petri.PetriUtils;

/**
 * @author Moqi 
 * ���������������,������Ϣ����Դ�����Ƴ����γɵ���
 */
public class InnerNet {
	
	private String source;
	private String sink;
	private List<String> places;
	private List<String> linkPlaces;
	//������Ǩ��(Note:��Ҫͨ������������ϻ��)
	private List<String> interTrans;
	private List<String> trans;
	private List<Flow> inLinkFlows;
	private List<Flow> outLinkFlows;
	private List<Flow> flows;
	private Map<String, String> tranLabelMap;
	private PetriUtils petriUtils;
	
	public InnerNet() {
		places = new ArrayList<String>();
		linkPlaces = new ArrayList<String>();
        interTrans = new ArrayList<String>();
		trans = new ArrayList<String>();
		inLinkFlows = new ArrayList<>();
		outLinkFlows = new ArrayList<>();
		flows = new ArrayList<Flow>();
		petriUtils = new PetriUtils();
	}
	
	/****************************Utils����******************************/
	
	public void addPlace(String place) {
		if (!places.contains(place)) {
			places.add(place);
		}
	}
	
	public void addLinkPlace(String place) {
		if (!linkPlaces.contains(place)) {
			linkPlaces.add(place);
		}
	}
	
	//����place�Ƴ�����(Note:ÿ��linkֻ��һ��Ψһsource��target)
	public void rovLinkPlace(String place) {
		if (linkPlaces.contains(place)) {
			for (int i = 0; i < inLinkFlows.size(); i++) {
				Flow tempFlow = inLinkFlows.get(i);
				String to = tempFlow.getFlowTo();
				if (place.equals(to)) {
					inLinkFlows.remove(i);
					break;
				}
			}
			for (int i = 0; i < outLinkFlows.size(); i++) {
				Flow tempFlow = outLinkFlows.get(i);
				String from = tempFlow.getFlowFrom();
				if (place.equals(from)) {
					outLinkFlows.remove(i);
					break;
				}
			}
		}
	}
	
	//��ӽ�����Ǩ(�����ظ����)
	public void addInterTran(String tran) {
		if (!interTrans.contains(tran)) {
			interTrans.add(tran);
		}
	}
	public void addInterTrans(List<String> trans) {
		for (String tran : trans) {
			if (!interTrans.contains(tran)) {
				interTrans.add(tran);
			}
		}
	}
	
	public void addTran(String tran) {
		if (!trans.contains(tran)) {
			trans.add(tran);
		}
	}
	
	public void rovTran(String tran) {
		trans.remove(tran);
	}
	
	public void addInLinkFlow(String flowFrom, String flowTo) {
		Flow flow = new Flow();
		flow.setFlowFrom(flowFrom);
		flow.setFlowTo(flowTo);
		inLinkFlows.add(flow);
	}
	
	//�Ƴ�����������
	public void rovInLinkFlow(String flowFrom, String flowTo) {
		for (int i = 0; i < inLinkFlows.size(); i++) {
			Flow tempFlow = inLinkFlows.get(i);
			String from = tempFlow.getFlowFrom();
			String to = tempFlow.getFlowTo();
			if (flowFrom.equals(from) && flowTo.equals(to)) {
				inLinkFlows.remove(i);
				break;
			}
		}
	}
	
	public void addOutLinkFlow(String flowFrom, String flowTo) {
		Flow flow = new Flow();
		flow.setFlowFrom(flowFrom);
		flow.setFlowTo(flowTo);
		outLinkFlows.add(flow);
	}
	
	//�Ƴ����������
	public void rovOutLinkFlow(String flowFrom, String flowTo) {
		for (int i = 0; i < outLinkFlows.size(); i++) {
			Flow tempFlow = outLinkFlows.get(i);
			String from = tempFlow.getFlowFrom();
			String to = tempFlow.getFlowTo();
			if (flowFrom.equals(from) && flowTo.equals(to)) {
				outLinkFlows.remove(i);
				break;
			}
		}
	}
	
	public void addFlow(Flow flow) {
		flows.add(flow);
	}
	
	//������from��to������
	public void addFlow(String flowFrom, String flowTo) {
		Flow flow = new Flow();
		flow.setFlowFrom(flowFrom);
		flow.setFlowTo(flowTo);
		flows.add(flow);
	}
	
	public void rovFlow(String flowFrom, String flowTo) {
		for (int i = 0; i < flows.size(); i++) {
			Flow tempFlow = flows.get(i);
			String from = tempFlow.getFlowFrom();
			String to = tempFlow.getFlowTo();
			if (flowFrom.equals(from) && flowTo.equals(to)) {
				flows.remove(i);
				break;
			}
		}
	}
	
	public void addFlows(List<Flow> tempFlows) {
		flows.addAll(tempFlows);
	}
	
	//ǰ�������Ʊ�Ǩ(eg., tran->ctrlPlace->ctrlTran->placeFrom)
	@SuppressWarnings("static-access")
	public void insertForwardCtrlTran(String placeFrom, String ctrlTran, String ctrlPlace) {

		List<String> preSet = petriUtils.getPreSet(placeFrom, getFlows());
		for (String tran : preSet) {
			addFlow(tran, ctrlPlace);
			rovFlow(tran, placeFrom);
		}
		addFlow(ctrlPlace, ctrlTran);
		addFlow(ctrlTran, placeFrom);
		
		//������ӵĿ��ƿ����ͱ�Ǩ
		getPlaces().add(ctrlPlace);
		getTrans().add(ctrlTran);
		// ���Ʊ�Ǩ��label����Id
		getTranLabelMap().put(ctrlTran, ctrlTran);

	}
		
	//���������Ʊ�Ǩ(eg., placeTo->ctrlTran->ctrlPlace->tran)
	@SuppressWarnings("static-access")
	public void insertBackCtrlTran(String placeTo, String ctrlTran, String ctrlPlace) {

		List<String> postSet = petriUtils.getPostSet(placeTo, getFlows());
		for (String tran : postSet) {
			addFlow(ctrlPlace, tran);
			rovFlow(placeTo, tran);
		}
		addFlow(placeTo, ctrlTran);
		addFlow(ctrlTran, ctrlPlace);
		
		//������ӵĿ��ƿ����ͱ�Ǩ
		getPlaces().add(ctrlPlace);
		getTrans().add(ctrlTran);
		// ���Ʊ�Ǩ��label����Id
		getTranLabelMap().put(ctrlTran, ctrlTran);

	}
	
	
	/*************************Get��Set����****************************/
	
	public String getSource() {
		return source;
	}
	public void setSource(String source) {
		this.source = source;
	}
	public String getSink() {
		return sink;
	}
	public void setSink(String sink) {
		this.sink = sink;
	}
	public List<String> getPlaces() {
		return places;
	}
	public void setPlaces(List<String> places) {
		this.places = places;
	}
	public List<String> getLinkPlaces() {
		return linkPlaces;
	}
	public void setLinkPlaces(List<String> linkPlaces) {
		this.linkPlaces = linkPlaces;
	}
	public List<String> getInterTrans() {
		return interTrans;
	}
	public void setInterTrans(List<String> interTrans) {
		this.interTrans = interTrans;
	}
	public List<String> getTrans() {
		return trans;
	}
	public void setTrans(List<String> trans) {
		this.trans = trans;
	}
	public List<Flow> getInLinkFlows() {
		return inLinkFlows;
	}
	public void setInLinkFlows(List<Flow> inLinkFlows) {
		this.inLinkFlows = inLinkFlows;
	}
	public List<Flow> getOutLinkFlows() {
		return outLinkFlows;
	}
	public void setOutLinkFlows(List<Flow> outLinkFlows) {
		this.outLinkFlows = outLinkFlows;
	}
	public List<Flow> getFlows() {
		return flows;
	}
	public void setFlows(List<Flow> flows) {
		this.flows = flows;
	}
	public Map<String, String> getTranLabelMap() {
		return tranLabelMap;
	}
	public void setTranLabelMap(Map<String, String> tranLabelMap) {
		this.tranLabelMap = tranLabelMap;
	}
	
	
}
