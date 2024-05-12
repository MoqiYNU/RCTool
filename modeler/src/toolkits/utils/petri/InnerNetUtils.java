package toolkits.utils.petri;

import java.util.ArrayList;
import java.util.List;

import org.apache.commons.collections4.CollectionUtils;

import toolkits.def.petri.Composition;
import toolkits.def.petri.Flow;
import toolkits.def.petri.ProNet;
import toolkits.utils.block.InnerNet;

public class InnerNetUtils {
	
	//��ȡԼ���Ĺ�����(Note:innerNet�Ŀ������в���������,��Ϣ������Դ��)
    public ProNet getReduceProNet(ProNet proNet, InnerNet innerNet) {
        
    	ProNet reduceProNet = new ProNet();
    	
    	reduceProNet.setSource(proNet.getSource());
    	
    	reduceProNet.setSinks(proNet.getSinks());
    	
    	reduceProNet.setPlaces(innerNet.getPlaces());
    	reduceProNet.addPlaces(proNet.getMsgPlaces());
    	reduceProNet.addPlaces(proNet.getResPlaces());
    	//������ӿ���(Note:Լ���б�����)
    	reduceProNet.addPlaces(getLinkPlaces(innerNet));
    	
    	reduceProNet.setMsgPlaces(proNet.getMsgPlaces());
    	
    	reduceProNet.setResPlaces(proNet.getResPlaces());
    	
    	reduceProNet.setLinkPlaces(getLinkPlaces(innerNet));
    	
    	reduceProNet.setResources(proNet.getResources()); 
    	reduceProNet.setInputMsgs(proNet.getInputMsgs());
    	reduceProNet.setOutputMsgs(proNet.getOutputMsgs());
    	reduceProNet.setTrans(innerNet.getTrans());
    	
    	reduceProNet.setCtrlTrans(proNet.getCtrlTrans());
    	//Note:���ǰ�������������Ŀ��Ʊ�Ǩ��
		reduceProNet.addCtrlTrans(getCtrlTrans(innerNet));
		
		reduceProNet.setFlows(innerNet.getFlows());
		//����������ӵ���
		List<Flow> inLinkFlows = innerNet.getInLinkFlows();
		for (Flow flow : inLinkFlows) {
			reduceProNet.addFlow(flow);
		}
		//���������ӵ���
		List<Flow> outLinkFlows = innerNet.getOutLinkFlows();
		for (Flow flow : outLinkFlows) {
			reduceProNet.addFlow(flow);
		}
		//�����Ϣ����Դ��
		reduceProNet.addFlows(proNet.getMsgAndResFlows());
		
		reduceProNet.setTranLabelMap(innerNet.getTranLabelMap());
		
		reduceProNet.setResProperMap(proNet.getResProperMap());
		
		reduceProNet.setReqResMap(proNet.getReqResMap());
		
		return reduceProNet;
		
	}
    
    //��ȡ�����е����ӿ�����
    public List<String> getLinkPlaces(InnerNet innerNet) {
		List<String> linkPlaces = new ArrayList<>();
		List<Flow> inLinkFlows = innerNet.getInLinkFlows();
		for (Flow flow : inLinkFlows) {
			String to = flow.getFlowTo();
			if (!linkPlaces.contains(to)) {
				linkPlaces.add(to);
			}
		}
		return linkPlaces;
	}
    
    //��ȡ��������ǰ�������������Ŀ��Ʊ�Ǩ��(Note:��ctrlǰ׺��ʼ��Ǩ)
    public List<String> getCtrlTrans(InnerNet innerNet) {
		List<String> ctrlTrans = new ArrayList<>();
		List<String> trans = innerNet.getTrans();
		for (String tran : trans) {
			if (tran.length() > 4 && tran.substring(0, 4).equals("ctrl")) {
				ctrlTrans.add(tran);
			}
		}
		return ctrlTrans;
	}
	
	/***********************��ȡһ�������������**************************/
	
	//��ȡһ���������Ӧ������
	public List<InnerNet> getInnerNets(List<ProNet> proNets) {
		List<InnerNet> innerNets = new ArrayList<>();
		Composition composition = new Composition();
		composition.setProNets(proNets);//������Ҫ����
		ProNet compNet = composition.compose();
		List<String> syncInterTrans = getSyncInterTrans(compNet);
        for (ProNet proNet : proNets) {
			InnerNet innerNet = proNet.getInnerNet();
			//������Ǩ����Ҫ������ϼ���õ�
			innerNet.addInterTrans(proNet.getAsynInterTrans());
			innerNet.addInterTrans((List<String>) CollectionUtils.intersection(syncInterTrans, proNet.getTrans()));
			innerNets.add(innerNet);
		}
        return innerNets;
	}
	
	//��ȡ������е�ͬ����Ǩ��
	public List<String> getSyncInterTrans(ProNet compNet) {
		List<String> syncInterTrans = new ArrayList<>();
		List<String> trans = compNet.getTrans();
		for (String tran : trans) {
			if (tran.contains("_")) {
				String[] mergeTrans = tran.split("\\_");
				for (int i = 0; i < mergeTrans.length; i++) {
					//�����ظ���ͬ����Ǩ(һ����Ǩ���Բ�����ͬ������)
					if (!syncInterTrans.contains(mergeTrans[i])) {
						syncInterTrans.add(mergeTrans[i]);
					}
				}
			}
		}
		return syncInterTrans;
	}
	
	
    /*************************��ȡ����������****************************/
	
	public InnerNet genInverNet(InnerNet innerNet) {
		InnerNet inverNet = new InnerNet();
		inverNet.setSource(innerNet.getSink());
		inverNet.setSink(innerNet.getSource());
		inverNet.setPlaces(innerNet.getPlaces());
		inverNet.setLinkPlaces(innerNet.getLinkPlaces());
		inverNet.setInterTrans(innerNet.getInterTrans());
		inverNet.setTrans(innerNet.getTrans());
		inverNet.setTranLabelMap(innerNet.getTranLabelMap());
		List<Flow> inverFlows = new ArrayList<Flow>();
        for (Flow flow : innerNet.getFlows()) {
			Flow inverFlow = new Flow();
			inverFlow.setFlowFrom(flow.getFlowTo());
			inverFlow.setFlowTo(flow.getFlowFrom());
			inverFlows.add(inverFlow);
		}
        //inverNet.setInLinkFlows(innerNet.getInLinkFlows());
        //inverNet.setOutLinkFlows(innerNet.getOutLinkFlows());
        inverNet.setFlows(inverFlows);
        return inverNet;
	}
	

}
