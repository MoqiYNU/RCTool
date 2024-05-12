package toolkits.def.petri;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;

import org.apache.commons.collections4.CollectionUtils;

import toolkits.utils.petri.PetriUtils;
import toolkits.utils.plan.MsgPlaceBag;

import org.apache.commons.collections4.MultiValuedMap;
import org.apache.commons.collections4.multimap.ArrayListValuedHashMap;

/**
 * @author Moqi
 * �������ɸ����������첽���
 */
public class Composition {
	
	private List<ProNet> proNets;//���ϲ�������
	private List<String> genSyncTrans;//ͬ����Ǩ��
	
	public Composition() {
		proNets = new ArrayList<ProNet>();
		genSyncTrans = new ArrayList<String>();
	}

	public List<ProNet> getProNets() {
		return proNets;
	}
	public void setProNets(List<ProNet> proNets) {
		this.proNets = proNets;
	}
	
	
	/**************************��϶��������(ͬʱ����ͬ�����첽ͨ��)*************************/
	
	public ProNet compose() {
		int size = proNets.size();
		//System.out.println("PN size: " + size);
		if (size == 1) {//1.ֻ��һ��������
			//Note:������г�ʼ��ʶ�б��뺬��Դ,�����޷�ִ��
			proNets.get(0).getSource().addPlaces(proNets.get(0).getResources());
			return proNets.get(0);
		}else {//2.����������������
			ProNet proNet = composeTwoProNets(proNets.get(0), proNets.get(1));
			for (int i = 2; i < size; i++) {
				//System.out.println("Compose i th PN: " + i);
				proNet = composeTwoProNets(proNet, proNets.get(i));	
			}
			//Note:������г�ʼ��ʶ�б��뺬��Դ,�����޷�ִ��
			proNet.getSource().addPlaces(proNet.getResources());
			return proNet;
		}
	}
		
	// �첽��Ϲ�����proNet1��proNet2
	public ProNet composeTwoProNets(ProNet proNet1, ProNet proNet2) {
		
		//������������������
		List<String> sourPlaces = new ArrayList<String>();
		List<Marking> sinks = new ArrayList<Marking>();
		List<String> places = new ArrayList<String>();
		List<String> msgPlaces = new ArrayList<String>();
		List<String> resPlaces = new ArrayList<String>();
		List<String> linkPlaces = new ArrayList<String>();
		List<String> resources = new ArrayList<String>();
		List<String> trans = new ArrayList<String>();
		List<String> ctrlTrans = new ArrayList<String>();
		List<Flow> flows = new ArrayList<Flow>();
		Map<String, String> tranLabelMap = new HashMap<String, String>();
		Map<String, Integer> resProperMap = new HashMap<String, Integer>();
		Map<String, List<String>> reqResMap = new HashMap<String, List<String>>();
		
		//1.��proNet1��proNet2����γɳ�ʼ��ʶ.......................
		sourPlaces.addAll(proNet1.getSource().getPlaces());
		sourPlaces.addAll(proNet2.getSource().getPlaces());
		Marking source = new Marking();
		source.addPlaces(sourPlaces);
		
		//2.�ϲ�Place:�����ظ�����Ϣ/��Դ����...........................
		List<String> places1 = proNet1.getPlaces();
		for (String place : places1) {
			if (!places.contains(place)) {
				places.add(place);
			}
		}
		List<String> places2 = proNet2.getPlaces();
		for (String place : places2) {
			if (!places.contains(place)) {
				places.add(place);
			}
		}
		
		//3.��Ǩ��.............................................
		
		//3.1���proNet1��proNet2�б�Ǩ(��Id��ʶ)
		List<String> trans1 = proNet1.getTrans();
		List<String> trans2 = proNet2.getTrans();
		
		//3.2��ȡ��Ǩ������
		List<String> syncTrans1 = getSyncTrans1(trans1, trans2, proNet1, proNet2);
		List<String> syncTrans2 = getSyncTrans2(trans1, trans2, proNet1, proNet2);
		//System.out.println("Sync Acts: " + syncActs1 + " " + syncActs2);
		
		//Note:MultiValuedMap������key,��Mapֻ����1��Key
		MultiValuedMap<String, String> syncMap1 = new ArrayListValuedHashMap<>();
		MultiValuedMap<String, String> syncMap2 = new ArrayListValuedHashMap<>();
		
		//3.3���ñ�Ǩ��(ͬ��Ǩ����label��ʶ)
		for (String tran1 : trans1) {
			if (!syncTrans1.contains(tran1)) {
				trans.add(tran1);
				tranLabelMap.put(tran1, getLabel(proNet1.getTranLabelMap(), tran1));
			}
		}
		
		for (String tran2 : trans2) {
			if (!syncTrans2.contains(tran2)) {
				trans.add(tran2);
				tranLabelMap.put(tran2, getLabel(proNet2.getTranLabelMap(), tran2));
			}
		}
		
        for (String syncTran1 : syncTrans1) {
        	//syncTrans�洢proNet2����syncTran1ͬ��(�����ͬ)��Ǩ�Ƽ�
        	List<String> syncTrans = new ArrayList<String>();
        	String label1 = getLabel(proNet1.getTranLabelMap(), syncTran1);
        	for (String syncTran2 : syncTrans2) {
        		String label2 = getLabel(proNet2.getTranLabelMap(), syncTran2);
        		if (label1.equals(label2)) {
        			syncTrans.add(syncTran2);
				}
    		}
        	
        	if (genSyncTrans.contains(syncTran1)) {
				genSyncTrans.remove(syncTran1);
			}
        	
        	for (String syncTran : syncTrans) {
        		
        		if (genSyncTrans.contains(syncTran)) {
					genSyncTrans.remove(syncTran);
				}
        		
        		//ͬ����ǨId�ϲ�:a_b
    			String genSyncTran = syncTran1 + "_" + syncTran;
    			syncMap1.put(syncTran1, genSyncTran);
    			syncMap2.put(syncTran, genSyncTran);
    			trans.add(genSyncTran);
    			tranLabelMap.put(genSyncTran, label1);
    			
    			genSyncTrans.add(genSyncTran);
			}
		}
		
		/**ֻ�����첽��Ϣ�������
		 * for (String tran1 : trans1) { trans.add(tran1); tranLabelMap.put(tran1,
		 * getLabel(proNet1.getTranLabelMap(), tran1)); } for (String tran2 : trans2) {
		 * trans.add(tran2); tranLabelMap.put(tran2, getLabel(proNet2.getTranLabelMap(),
		 * tran2)); }
		 */
		
        //4.����Ǩ.............................................
        List<Flow> flows1 = proNet1.getFlows();
        for (Flow flow : flows1) {
			String flowFrom = flow.getFlowFrom();
			String flowTo = flow.getFlowTo();
			if (syncTrans1.contains(flowFrom)) {//flowFrom��ͬ����Ǩ
				
				List<String> labels = (List<String>) syncMap1.get(flowFrom);//��ȡ�ϲ���Ǩ����
				for (String label : labels) {
					Flow tempFlow = new Flow();
					tempFlow.setFlowFrom(label);
	  				tempFlow.setFlowTo(flowTo);
	  			    flows.add(tempFlow);
				}
				
			}else if (syncTrans1.contains(flowTo)) {//flowTo��ͬ����Ǩ
				
				List<String> labels = (List<String>) syncMap1.get(flowTo);//��ȡ�ϲ���Ǩ����
				//System.out.println("flowTo: "+ flowTo + " labels: " + labels);
				for (String label : labels) {
					Flow tempFlow = new Flow();
	  				tempFlow.setFlowFrom(flowFrom);
	  				tempFlow.setFlowTo(label);
	  				flows.add(tempFlow);
				}
				
			}else {//��ͬ��Ǩ��,ֱ�������
				
				flows.add(flow);
				
			}
		  }
        
          //����proNet2�е���(�����첽ͨ�źϲ�)
	      List<Flow> flows2 = proNet2.getFlows();
	      for (Flow flow : flows2) {
			String flowFrom = flow.getFlowFrom();
			String flowTo = flow.getFlowTo();
			if (syncTrans2.contains(flowFrom)) {
				
				List<String> labels = (List<String>) syncMap2.get(flowFrom);//��ȡ�ϲ���Ǩ����
				for (String label : labels) {
					Flow tempFlow = new Flow();
					tempFlow.setFlowFrom(label);
	  				tempFlow.setFlowTo(flowTo);
	  			    flows.add(tempFlow);
				}
				
			}else if (syncTrans2.contains(flowTo)) {
				
				List<String> labels = (List<String>) syncMap2.get(flowTo);//��ȡ�ϲ���Ǩ����
				for (String label : labels) {
					Flow tempFlow = new Flow();
	  				tempFlow.setFlowFrom(flowFrom);
	  				tempFlow.setFlowTo(label);
	  				flows.add(tempFlow);
				}
				
			}else {
				
				flows.add(flow);
				
			}
		}
        
        
		/**ֻ�����첽��Ϣ�������
		 * List<Flow> flows1 = proNet1.getFlows(); List<Flow> flows2 =
		 * proNet2.getFlows(); flows.addAll(flows1); flows.addAll(flows2);
		 */
  		
	    //5.��ֹ��ʶ.............................................
	    List<Marking> sinks1 = proNet1.getSinks();
	    List<Marking> sinks2 = proNet2.getSinks();
	    for (Marking marking1 : sinks1) {
	        List<String> finalPlaces1 = marking1.getPlaces();
			for (Marking marking2 : sinks2) {
				List<String> finalPlaces2 = marking2.getPlaces();
				Marking sink = new Marking();
				List<String> finalPlaces = new ArrayList<String>();
				finalPlaces.addAll(finalPlaces1);
				finalPlaces.addAll(finalPlaces2);
				sink.setPlaces(finalPlaces);
				sinks.add(sink);
			}
		}
        
        //System.out.println("Comp Final makrings: " + sink.getPlaces());
        
        //6.�ϲ���Ϣ����:�����ظ�.............................
  		List<String> msgPlaces1 = proNet1.getMsgPlaces();
  		for (String place : msgPlaces1) {
  			if (!msgPlaces.contains(place)) {
  				msgPlaces.add(place);
  			}
  		}
  		List<String> msgPlaces2 = proNet2.getMsgPlaces();
  		for (String place : msgPlaces2) {
  			if (!msgPlaces.contains(place)) {
  				msgPlaces.add(place);
  			}
  		}
  		
  	    //7.�ϲ���Դ����:�����ظ�.............................
  		List<String> resPlaces1 = proNet1.getResPlaces();
  		for (String place : resPlaces1) {
  			if (!resPlaces.contains(place)) {
  				resPlaces.add(place);
  			}
  		}
  		List<String> resPlaces2 = proNet2.getResPlaces();
  		for (String place : resPlaces2) {
  			if (!resPlaces.contains(place)) {
  				resPlaces.add(place);
  			}
  		}
  		
  	    //8.�ϲ����ӿ���.....................................
  		linkPlaces.addAll(proNet1.getLinkPlaces());
  		linkPlaces.addAll(proNet2.getLinkPlaces());
  		
  	    //9.�ϲ���Դ��������Դ����(���⹲����Դ�ظ�).............................
  		List<String> sharResPlaces = (List<String>) CollectionUtils.intersection(resPlaces1, resPlaces2);
  		List<String> resources1 = proNet1.getResources();
  		Map<String, Integer> resProperMap1 = proNet1.getResProperMap();
  		for (String res : resources1) {
  			resources.add(res);
  			resProperMap.put(res, resProperMap1.get(res));
  		}
  		List<String> resources2 = proNet2.getResources();
  		Map<String, Integer> resProperMap2 = proNet2.getResProperMap();
  		for (String res : resources2) {
  			if (sharResPlaces.contains(res)) {//����������Դ
				continue;
			}else {
				resources.add(res);
				resProperMap.put(res, resProperMap2.get(res));
			}
  		}
  		
  		//10.����������Դӳ��(���⹲����Դ�ظ�).............................
  		Map<String, List<String>> reqResMap1 = proNet1.getReqResMap();
  		Map<String, List<String>> reqResMap2 = proNet2.getReqResMap();
  		for (Entry<String, List<String>> entry : reqResMap1.entrySet()) {
  			String res = entry.getKey();
  			if (sharResPlaces.contains(res)) {
				List<String> reqTrans = new ArrayList<String>();
				reqTrans.addAll(reqResMap1.get(res));
				reqTrans.addAll(reqResMap2.get(res));
				reqResMap.put(res, reqTrans);
			}else {
				reqResMap.put(res, reqResMap1.get(res));
			}
  		}
  		for (Entry<String, List<String>> entry : reqResMap2.entrySet()) {
  			String res = entry.getKey();
  			if (sharResPlaces.contains(res)) {
				continue;
			}else {
				reqResMap.put(res, reqResMap2.get(res));
			}
  		}
  		
  		//11.�ϲ����Ʊ�Ǩ
  		ctrlTrans.addAll(proNet1.getCtrlTrans());
		ctrlTrans.addAll(proNet2.getCtrlTrans());
        
        ProNet compNet = new ProNet();
		compNet.setSource(source);
		compNet.setPlaces(places);
		compNet.setTrans(trans);
		compNet.setCtrlTrans(ctrlTrans);
		compNet.setFlows(flows);
		compNet.setSinks(sinks);
		compNet.setMsgPlaces(msgPlaces);
		compNet.setResPlaces(resPlaces);
		compNet.setLinkPlaces(linkPlaces);
		compNet.setResources(resources);
		compNet.setTranLabelMap(tranLabelMap);
		compNet.setResProperMap(resProperMap);
		compNet.setReqResMap(reqResMap);
		
		return compNet;
		
	}
	
	//��ȡ���������Ϣ������
	public List<MsgPlaceBag> getMsgPlaceBags(List<String> msgPlaces, List<Flow> flows) {
		List<MsgPlaceBag> msgPlaceBags = new ArrayList<>();
		for (String msgPlace : msgPlaces) {
			List<String> preSet = PetriUtils.getPreSet(msgPlace, flows);
			List<String> postSet = PetriUtils.getPostSet(msgPlace, flows);
			MsgPlaceBag bag = new MsgPlaceBag();
			bag.setPreSet(preSet);
			bag.setPostSet(postSet);
			msgPlaceBags.add(bag);
			//System.out.println("msgPlace: " + msgPlace + ", PreSet: " + preSet + ", PostSet: " + postSet);
		}
		return msgPlaceBags;
	}
	
	//��ȡproNet1��ͬ��Ǩ��
	public List<String> getSyncTrans1(List<String> trans1, List<String> trans2, 
			ProNet openNet1, ProNet openNet2) {
		List<String> syncTrans1 = new ArrayList<String>();
        for (String tran1 : trans1) {
			if (openNet1.getCtrlTrans().contains(tran1)) {//�ų����Ʊ�Ǩ 
			    continue; 
			}
			if (isSyncTran(tran1, trans2, openNet1, openNet2)) {
				syncTrans1.add(tran1);
			}
		}
        return syncTrans1;
	}
	
	//��ȡproNet2��ͬ��Ǩ��
	public List<String> getSyncTrans2(List<String> trans1, List<String> trans2, 
			ProNet openNet1, ProNet openNet2) {
		List<String> syncTrans2 = new ArrayList<String>();
        for (String tran2 : trans2) {
			if (openNet2.getCtrlTrans().contains(tran2)) {//�ų����Ʊ�Ǩ
				continue;
			}
			if (isSyncTran(tran2, trans1, openNet2, openNet1)) {
				syncTrans2.add(tran2);
			}
		}
        return syncTrans2;
	}
	
	//�ж�tran1�ǲ���ͬ��Ǩ��
	public boolean isSyncTran(String tran1, List<String> trans2, 
			ProNet openNet1, ProNet openNet2) {
		String label1 = getLabel(openNet1.getTranLabelMap(), tran1);
    	for (String tran2 : trans2) {
    		if (openNet2.getCtrlTrans().contains(tran2)) {//�ų����Ʊ�Ǩ
				continue;
			}
    		String label2 = getLabel(openNet2.getTranLabelMap(), tran2);
    		if (label1.equals(label2)) {
    			return true;
			}
		}
    	return false;
	}
	
	//���tran��Ӧ��label(Ĭ��Ϊid)
	public String getLabel(Map<String, String> tranLabelMap, String tran) {
		String label = tranLabelMap.get(tran);
		return label;
	}

	
}
