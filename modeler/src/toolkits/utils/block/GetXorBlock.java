package toolkits.utils.block;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import org.apache.commons.collections4.Bag;
import org.apache.commons.collections4.bag.HashBag;

import toolkits.def.petri.Flow;
import toolkits.utils.petri.PetriUtils;

/**
 * @author Moqi
 * ͨ��DFS����������ѡ���
 */
public class GetXorBlock {
	
	//����Ԫѡ�񲿼�
	private List<Block> metaXORBlocks;
	private List<String> orSplits;
	private List<String> orJoins;
	
	public GetXorBlock() {
		metaXORBlocks = new ArrayList<Block>();
		orSplits = new ArrayList<>();
		orJoins = new ArrayList<>();
	}
	
	public List<Block> getMetaXORBlocks() {
		return metaXORBlocks;
	}
	
	public List<String> getOrSplits() {
		return orSplits;
	}

	public List<String> getOrJoins() {
		return orJoins;
	}

	public void compute(InnerNet net, List<Block> loopBlocks) {
		
		//����ǰ����ջ���
		metaXORBlocks.clear();
		orSplits.clear();
		orJoins.clear();
		
		// 1.����ѭ�����д���ڳ����Ļ����������ڵĻ��
		List<String> entryActsInLoop = new ArrayList<String>();
		List<String> exitActsInLoop = new ArrayList<String>();
		for (Block block : loopBlocks) {
			entryActsInLoop.addAll(block.getEntryPost());
			exitActsInLoop.addAll(block.getExitPre());
		}
		
		// 2.���ÿ����֧�������м���Ԫѡ���
		List<String> places = net.getPlaces();
		for (String place : places) {
			//��ȡ��place����������(Note:�ų�����ѭ������)
			List<Flow> splitFlows = computeSplitFlows(place, net.getFlows(), entryActsInLoop);
			if (splitFlows.size() > 1) {//2.1 Ϊ��֧����
				orSplits.add(place);
				Block block = creatMetaXORBlock(place, splitFlows, net.getFlows());
				if (block != null) {
					metaXORBlocks.add(block);
				}
			}
			//��ȡ����place������(Note:�ų���ѭ������)
			List<Flow> joinFlows = computeJoinFlows(place, net.getFlows(), exitActsInLoop);
			if (joinFlows.size() > 1) {//2.2 Ϊ��Ͽ���
				orJoins.add(place);
			}
		}
		
	}
	
	//�����place����������(Note:�ų���ѭ������)
	private List<Flow> computeSplitFlows(String place, List<Flow> flows, List<String> entryActsInLoop) {
		
		List<Flow> succFlows = new ArrayList<Flow>();
		for (Flow flow : flows) {
			String from = flow.getFlowFrom();
			String to = flow.getFlowTo();
			if (place.equals(from) && !entryActsInLoop.contains(to)) {
				succFlows.add(flow);
			}
		}
		return succFlows;
	}
	
	//���㵽��place������(Note:�ų���ѭ������)
	private List<Flow> computeJoinFlows(String place, List<Flow> flows, List<String> exitActsInLoop) {
		
		List<Flow> reachFlows = new ArrayList<Flow>();
		for (Flow flow : flows) {
			String from = flow.getFlowFrom();
			String to = flow.getFlowTo();
			if (place.equals(to) && !exitActsInLoop.contains(from)) {
				reachFlows.add(flow);
			}
		}
		return reachFlows;
	}
	
	//����Ԫѡ���
	public Block creatMetaXORBlock(String place, List<Flow> splitFlows, List<Flow> flows) {
		
		List<String> exits = new ArrayList<String>();
		List<String> exitsGen = new ArrayList<String>();
		for (Flow flow : splitFlows) {//���ÿ����֧�����м���
			String act = flow.getFlowTo();
			List<String> preSet = PetriUtils.getPreSet(act, flows);
			List<String> postSet = PetriUtils.getPostSet(act, flows);
			exitsGen.addAll(postSet);
			if (preSet.size() == 1 && postSet.size() == 1) {
				exits.add(postSet.get(0));
			}
		}
		
		/**C1:���һ��Ԫѡ���XOR2(Ԫѡ����),������Bagȷ�ϲ��ظ�exitsGen��..............................*/
		Bag<String> bagGen = new HashBag<String>(exitsGen);
		Set<String> uniqueSetGen = bagGen.uniqueSet();
		if (uniqueSetGen.size() == 1) {//��Ӧ����������XOR2
			Block block = new Block();
			block.setEntry(place);
			List<String> actsInMetaXor = PetriUtils.getPostSet(place, flows);
			for (String actInMetaXor : actsInMetaXor) {
				block.addEntryPost(actInMetaXor);
				block.addExitPre(actInMetaXor);
			}
			block.setType("XOR");
			block.setExit(exitsGen.get(0));
			//System.out.println("actInMetaXor: " + actsInMetaXor + ", uniqueSetGen: " + uniqueSetGen);
			return block;
		}
		
		/**C2:���XOR1(Ԫѡ��ǰ��),������Bagȷ�ϲ��ظ�exits��...................................*/
		Bag<String> bag = new HashBag<String>(exits);
		Set<String> uniqueSet = bag.uniqueSet();
		if (uniqueSet.size() == 0) {
			return null;
		}else {
			for (String exit : uniqueSet) {
				if (bag.getCount(exit) > 1) {
					if (!isValidExit(exit, flows)) {
						continue;
					}
					Block block = new Block();
					block.setEntry(place);
					List<String> actsInMetaXor = PetriUtils.getPreSet(exit, flows);
					for (String actInMetaXor : actsInMetaXor) {
						block.addEntryPost(actInMetaXor);
						block.addExitPre(actInMetaXor);
					}
					block.setType("XOR");
					block.setExit(exit);
					//System.out.println("actInMetaXor: " + actsInMetaXor + ", uniqueSet: " + uniqueSet);
					return block;
				}else {
					continue;
				}
			}
		}
	    return null;
		
	}
	
	//�ж�exit����Ƿ���Ч,�μ�����������XOR1
	public boolean isValidExit(String exit, List<Flow> flows) {
		
		List<String> entries = new ArrayList<String>();
		List<String> preSet = PetriUtils.getPreSet(exit, flows);
		for (String tran : preSet) {
			List<String> places = PetriUtils.getPreSet(tran, flows);
			entries.addAll(places);
		}
		//����Bagȥ��entries
		Bag<String> bag = new HashBag<String>(entries);
		Set<String> uniqueSet = bag.uniqueSet();
		if (uniqueSet.size() == 1) {
			return true;
		}
		return false;
		
	}
	
	//�����place�����ı�Ǩ��(Note:�ų���ѭ������)
	public List<String> getToTransNotInLoop(String place, InnerNet net, List<Block> loopBlocks) {
		
		List<String> trans = new ArrayList<String>();
		//����ѭ�������д���ڳ����Ļ����������ڵĻ��
		List<String> entryActsInLoop = new ArrayList<String>();
		List<String> exitActsInLoop = new ArrayList<String>();
		for (Block block : loopBlocks) {
			entryActsInLoop.addAll(block.getEntryPost());
			exitActsInLoop.addAll(block.getExitPre());
		}
		//��place����������(�ų���ѭ������)
		List<Flow> splitFlows = computeSplitFlows(place, net.getFlows(), entryActsInLoop);
		for (Flow flow : splitFlows) {
			String tran = flow.getFlowTo();
			trans.add(tran);
		}
		return trans;
	}
	
}
