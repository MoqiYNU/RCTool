package toolkits.utils.block;

import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.util.Queue;

import toolkits.def.petri.Flow;
import toolkits.def.petri.ProNet;
import toolkits.utils.petri.InnerNetUtils;
import toolkits.utils.petri.PetriUtils;

/**
 * *@author Moqi
 * �������������ص�Utils
 */
public class ProTreeUtils {

	private ProTreeBuilder proTreeBuilder;

	public ProTreeUtils() {
		proTreeBuilder = new ProTreeBuilder();
	}

	/**************************** �ӹ����������ɹ����� ******************************/

	public List<ProTree> genProTrees(List<ProNet> proNets) throws Exception {
		List<ProTree> proTrees = new ArrayList<>();
		InnerNetUtils innerNetUtils = new InnerNetUtils();
		List<InnerNet> innerNets = innerNetUtils.getInnerNets(proNets);
		for (int i = 0; i < innerNets.size(); i++) {
			// 1.��ȡproNet����(Note:�������Ƴ������������ӿ���Ȼ���Ƴ��������,�������ӽ����´��󲢷�)
			InnerNet innerNet1 = rovLinkPlaces(innerNets.get(i));
			InnerNet innerNet = rovRedPlaces(innerNet1);
			// dotUtils.innerNet2Dot(proNets.get(i).getCtrlTrans(), innerNet, "ipn" + i);
			// 2.��ó�ʼ������
			ProTree initProTree = proTreeBuilder.compute(innerNet);
			// dotUtils.pt2Dot(initProTree, proNet.getTranLabelMap(), "pt" + index);
			// 3.ѹ����ʼ������
			ProTree proTree = compress(initProTree);
			// 4.���ù������е�ͬ������
			List<String> links = proNets.get(i).getLinkPlaces();
			for (String link : links) {// ͬ������ǰ���Ϻ󼯾�Ϊһ����Ǩ
				String from = PetriUtils.getPreSet(link, proNets.get(i).getFlows()).get(0);
				String to = PetriUtils.getPostSet(link, proNets.get(i).getFlows()).get(0);
				proTree.getLinks().put(from, to);
			}
			// 5.���ù������е��ڲ���Լ�
			List<String> trans = innerNets.get(i).getTrans();
			for (String tran : trans) {
				if (!innerNets.get(i).getInterTrans().contains(tran)
						&& !proNets.get(i).getCtrlTrans().contains(tran)) {
					proTree.addInnerTran(tran);
				}
			}
			proTrees.add(proTree);
			// dotUtils.proTree2Dot(proTree, proNets.get(i).getTranLabelMap(), "cpt" + i);
		}
		return proTrees;
	}

	/******************************** Ԥ�������� **********************************/

	// 1.�����ɹ�����֮ǰ,�������Ƴ����������������ӿ���,�����Ӱ����㲢�������������
	public InnerNet rovLinkPlaces(InnerNet net) {

		InnerNet interNet = new InnerNet();// ����������

		// Note: ���ӿ�����Ϊ��ɾ������
		List<String> rovPlaces = new ArrayList<String>();
		rovPlaces.addAll(net.getLinkPlaces());

		// 1.����interNet�е�����
		List<Flow> noRovFlows = new ArrayList<Flow>();
		List<Flow> flows = net.getFlows();
		for (Flow flow : flows) {
			String from = flow.getFlowFrom();
			String to = flow.getFlowTo();
			if (rovPlaces.contains(from) || rovPlaces.contains(to)) {
				continue;
			} else {
				noRovFlows.add(flow);
			}
		}

		// 2.����interNet�еĿ���
		List<String> places = net.getPlaces();
		for (Flow flow : noRovFlows) {
			String from = flow.getFlowFrom();
			String to = flow.getFlowTo();
			if (places.contains(from)) {
				interNet.addPlace(from);
			}
			if (places.contains(to)) {
				interNet.addPlace(to);
			}
		}

		// 3.����interNet�еı�Ǩ
		List<String> trans = net.getTrans();
		for (Flow flow : noRovFlows) {
			String from = flow.getFlowFrom();
			String to = flow.getFlowTo();
			if (trans.contains(from)) {
				interNet.addTran(from);
			}
			if (trans.contains(to)) {
				interNet.addTran(to);
			}
		}

		// ����interNet
		interNet.setSource(net.getSource());
		interNet.setSink(net.getSink());
		interNet.setLinkPlaces(net.getLinkPlaces());
		interNet.setInterTrans(net.getInterTrans());
		interNet.setInLinkFlows(net.getInLinkFlows());
		interNet.setOutLinkFlows(net.getOutLinkFlows());
		interNet.setFlows(noRovFlows);
		interNet.setTranLabelMap(net.getTranLabelMap());
		return interNet;

	}

	// 2)���Ƴ����ӿ��������Ƴ��������������������
	public InnerNet rovRedPlaces(InnerNet net) {

		InnerNet interNet = new InnerNet();// ����������

		List<String> rovPlaces = new ArrayList<String>();
		List<String> places = net.getPlaces();
		for (String place : places) {
			List<String> fromTrans = PetriUtils.getPreSet(place, net.getFlows());
			List<String> toTrans = PetriUtils.getPostSet(place, net.getFlows());
			if (fromTrans.size() == 1 && toTrans.size() == 1) {
				String fromTran = fromTrans.get(0);
				String toTran = toTrans.get(0);
				// ��Ӳ�����������Ŀ���
				if (PetriUtils.getPostSet(fromTran, net.getFlows()).size() > 1
						&& PetriUtils.getPreSet(toTran, net.getFlows()).size() > 1) {
					rovPlaces.add(place);
				}
			}
		}

		// 1.����interNet�е�����
		List<Flow> noRovFlows = new ArrayList<Flow>();
		List<Flow> flows = net.getFlows();
		for (Flow flow : flows) {
			String from = flow.getFlowFrom();
			String to = flow.getFlowTo();
			if (rovPlaces.contains(from) || rovPlaces.contains(to)) {
				continue;
			} else {
				noRovFlows.add(flow);
			}
		}

		// 2.����interNet�еĿ���
		for (Flow flow : noRovFlows) {
			String from = flow.getFlowFrom();
			String to = flow.getFlowTo();
			if (places.contains(from)) {
				interNet.addPlace(from);
			}
			if (places.contains(to)) {
				interNet.addPlace(to);
			}
		}

		// 3.����interNet�еı�Ǩ
		List<String> trans = net.getTrans();
		for (Flow flow : noRovFlows) {
			String from = flow.getFlowFrom();
			String to = flow.getFlowTo();
			if (trans.contains(from)) {
				interNet.addTran(from);
			}
			if (trans.contains(to)) {
				interNet.addTran(to);
			}
		}

		// ����interNet
		interNet.setSource(net.getSource());
		interNet.setSink(net.getSink());
		interNet.setLinkPlaces(net.getLinkPlaces());
		interNet.setInterTrans(net.getInterTrans());
		interNet.setInLinkFlows(net.getInLinkFlows());
		interNet.setOutLinkFlows(net.getOutLinkFlows());
		interNet.setFlows(noRovFlows);
		interNet.setTranLabelMap(net.getTranLabelMap());
		return interNet;

	}

	/******************************** ѹ�������� **********************************/

	// ������������ѹ��,�Ա�֤����ÿ�����ӽڵ��븸�׽ڵ�����Ͳ�ͬ
	public ProTree compress(ProTree proTree) {

		// �������ʵĶ���visitingQueue����proTree���
		Queue<ProTree> visitingQueue = new LinkedList<>();
		visitingQueue.offer(proTree);

		// ��������
		while (visitingQueue.size() > 0) {

			ProTree proTreeFrom = visitingQueue.poll();

			// 1.��proTreeFrom����ѹ��,��ֱ�ӷ���
			Node compNode = isCompress(proTreeFrom);
			if (compNode == null) {
				return proTreeFrom;
			}

			// 2.����ѹ��,���½�������(Note:�����½��������,��Ϊ����*******)
			Node compNodeFather = getFatherNode(proTreeFrom, compNode);
			// �洢ѹ���������еĽڵ�
			List<Node> compNodes = new ArrayList<Node>();
			for (Node node : proTreeFrom.getNodes()) {
				if (node.getId().equals(compNode.getId())) {// ������ѹ���ڵ�
					continue;
				}
				if (node.getId().equals(compNodeFather.getId())) {// �������и��׽ڵ�����ĺ��ӽڵ�
					// �洢ѹ���󸸽ڵ�ĺ��ӽڵ�
					List<String> updaChaNodesFather = new ArrayList<String>();
					for (String chaNode : compNodeFather.getChaNodes()) {
						if (chaNode.equals(compNode.getId())) {
							updaChaNodesFather.addAll(compNode.getChaNodes());
						} else {
							updaChaNodesFather.add(chaNode);
						}
					}
					// Note:�����½�(��Ϊ����),�������
					Node newCompNodeFather = new Node();
					newCompNodeFather.setId(compNodeFather.getId());
					newCompNodeFather.setType(compNodeFather.getType());
					newCompNodeFather.setChaNodes(updaChaNodesFather);
					compNodes.add(newCompNodeFather);
				} else {
					compNodes.add(node);
				}
			}

			// ������ѹ��������
			ProTree compProTree = new ProTree();
			compProTree.setNodes(compNodes);
			visitingQueue.offer(compProTree);

		}
		return null;

	}

	// �ж�pt�ܷ�ѹ��,������һ���ڵ������������丸�׽ڵ�һ��
	public Node isCompress(ProTree pt) {
		List<Node> nodes = pt.getNodes();
		for (Node node : nodes) {// Ҷ�ӽڵ�����ѹ��
			if (node.getType().equals("leaf")) {
				continue;
			}
			Node nodeFather = getFatherNode(pt, node);
			if (nodeFather == null) {// ���ڵ�Ϊ������ѹ��
				continue;
			}
			if (nodeFather.getType().equals(node.getType())) {
				return node;
			}
		}
		return null;
	}

	/*********** ���������ֽ�ΪƬ�� (�Զ������Ա��������ظ�Ƭ��) ***********************/

	public List<ProTree> genFragments(ProTree proTree/* , InnerNet innerNet */) throws Exception {

		// ����XOR�ڵ�ֽ��õ�Ƭ��
		List<ProTree> fragments = new ArrayList<>();

		// �������ʵĶ���visitingQueue����proTree���
		Queue<ProTree> visitingQueue = new LinkedList<>();
		visitingQueue.offer(proTree);
		// ��������
		while (visitingQueue.size() > 0) {

			ProTree proTreeFrom = visitingQueue.poll();

			Node xorNode = isDecompose(proTreeFrom);

			if (xorNode == null) {// 1.proTreeFrom���ɷֽ�,��ֱ����ӵ�Ƭ���в���������ѭ��
				// Note:����Ƭ����ѹ������
				fragments.add(compress(proTreeFrom));
				continue;
			}

			// 2.proTreeFrom�ɷֽ�,�����Ȼ���丸�׽ڵ�
			Node xorNodeFather = getFatherNode(proTreeFrom, xorNode);

			if (xorNodeFather == null) {// 2.1�����׽ڵ�Ϊ��,����ÿ�����ӽڵ�Ϊ������һ�Ź�����

				List<String> chaNodes = xorNode.getChaNodes();
				for (String chaNode : chaNodes) {
					List<Node> desc = getDesc(proTree, chaNode);
					ProTree depProTree = new ProTree();// �ֽ�������
					depProTree.setNodes(desc);
					visitingQueue.offer(depProTree);
				}

			} else {// 2.2�����׽ڵ�ǿ�,����xorNode�ڵ��ÿ�����ӽڵ�����һ�Ŷ�ӦƬ��

				// System.out.println("test............................");

				List<String> chaNodes = xorNode.getChaNodes();
				for (String chaNode : chaNodes) {

					/*
					 * if (chaNode.getType().equals("leaf")) {
					 * System.out.println("chaNode: " +
					 * innerNet.getTranLabelMap().get(chaNode.getIdf()));
					 * }else {
					 * System.out.println("chaNode: " + chaNode.getIdf());
					 * }
					 */

					// 2.2.1 ����Ƭ���нڵ㼰��������ӽڵ㼯
					List<Node> depNodes = new ArrayList<Node>();
					for (Node node : proTreeFrom.getNodes()) {
						// 1.�Ǹ��׽ڵ�,���亢�ӽڵ���xorNode�滻ΪchaNode
						if (node.getId().equals(xorNodeFather.getId())) {
							List<String> updaChaNodesFather = new ArrayList<String>();
							List<String> chaNodesFather = xorNodeFather.getChaNodes();
							for (String chaNodeFather : chaNodesFather) {
								if (chaNodeFather.equals(xorNode.getId())) {
									// System.out.println("add node: " + chaNode.getIdf());
									updaChaNodesFather.add(chaNode);
								} else {
									updaChaNodesFather.add(chaNodeFather);
								}
							}
							// Note:�����½�,�������
							Node newXorNodeFather = new Node();
							newXorNodeFather.setId(xorNodeFather.getId());
							newXorNodeFather.setType(xorNodeFather.getType());
							newXorNodeFather.setChaNodes(updaChaNodesFather);
							depNodes.add(newXorNodeFather);
						} else {// 2.����ֱ�����
							depNodes.add(node);
						}
					}

					// 2.2.2 �����ֽ������
					ProTree depProTree = new ProTree();
					depProTree.setNodes(depNodes);

					// 2.2.3 �Ƴ�xorNode�ڵ�
					depProTree.removeNode(xorNode);

					// 2.2.4 �Ƴ���chaNode�ڵ㼰������ڵ�
					List<String> restNodes = getRestNodes(chaNodes, chaNode);
					for (String restNode : restNodes) {
						List<Node> desc = getDesc(proTree, restNode);
						for (Node descNode : desc) {
							// System.out.println("remove node:" + descNode.getIdf());
							depProTree.removeNode(descNode);
						}
					}

					/*
					 * List<Node> nodes = depProTree.getNodes();
					 * for (Node node : nodes) {
					 * if (node.getType().equals("leaf")) {
					 * System.out.println("updated nodes: " +
					 * innerNet.getTranLabelMap().get(node.getIdf()));
					 * }else {
					 * System.out.println("updated nodes: " + node.getIdf());
					 * }
					 * }
					 */

					// 2.2.4��ӵ�j���ֽ��������ʶ���
					visitingQueue.offer(depProTree);

				}
			}
		}
		return fragments;

	}

	/****************************** ������Utils ********************************/

	// ��ȡchaNodes�г�node��ڵ㼯
	public List<String> getRestNodes(List<String> chaNodes, String node) {
		List<String> restNodes = new ArrayList<String>();
		for (String chaNode : chaNodes) {
			if (chaNode.equals(node)) {
				continue;
			}
			restNodes.add(chaNode);
		}
		return restNodes;

	}

	// ��ȡ��nodeΪ��������Ҷ������ڵ��Id
	public List<String> getLeafDesc(ProTree proTree, Node node) {
		List<String> desc = new ArrayList<>();
		Queue<Node> queue = new LinkedList<>();
		queue.add(node);// Note:�������Լ�(����Ҷ�ӽ��)
		while (queue.size() > 0) {
			Node tempNode = queue.poll();
			if (tempNode.getType().equals("leaf")) {
				desc.add(tempNode.getId());
			} else {
				List<String> chaNodes = tempNode.getChaNodes();
				for (String chaNode : chaNodes) {
					queue.add(getNodeById(proTree, chaNode));
				}
			}
		}
		return desc;
	}

	// ��ȡ������С����And���Ƚ��Ŀ��ƽ��And-Split��And-Join
	public List<String> getCtrlTransFromMinCommAndAncestor(ProTree proTree, String node1, String node2) {
		List<String> ctrlTrans = new ArrayList<>();
		String minCommAndAncestor = getMinCommAndAncestor(proTree, node1, node2);
		Node fatherNode = getFatherNode(proTree, minCommAndAncestor);
		List<String> chaNodes = fatherNode.getChaNodes();
		for (int i = 0; i < chaNodes.size(); i++) {
			if (chaNodes.get(i).equals(minCommAndAncestor)) {
				ctrlTrans.add(chaNodes.get(i - 1));
				ctrlTrans.add(chaNodes.get(i + 1));
			}
		}
		return ctrlTrans;
	}

	// ��ȡ���node1��node2����С�Ĺ���And���Ƚ��
	public String getMinCommAndAncestor(ProTree proTree, String node1, String node2) {
		List<String> ancestor1 = getAncestor(proTree, node1);
		List<String> ancestor2 = getAncestor(proTree, node2);
		for (String node : ancestor1) {
			if (ancestor2.contains(node)) {
				return node;
			}
		}
		return null;
	}

	// ��ȡ��node����������AND���Ƚ������
	public List<String> getAncestor(ProTree proTree, String nodeId) {
		List<String> ancestor = new ArrayList<>();
		Queue<Node> queue = new LinkedList<>();
		Node fatherNode = getFatherNode(proTree, nodeId);
		queue.add(fatherNode);// Note:�������Լ�
		if (fatherNode.getType().equals("AND")) {
			ancestor.add(fatherNode.getId());
		}
		while (queue.size() > 0) {
			Node tempNode = queue.poll();
			Node tempFatherNode = getFatherNode(proTree, tempNode);
			queue.add(tempFatherNode);
			if (tempFatherNode.getType().equals("AND")) {
				ancestor.add(tempFatherNode.getId());
			}
		}
		return ancestor;
	}

	// ��ȡid��Ӧ�������еĽ��
	public Node getNodeById(ProTree proTree, String idf) {
		List<Node> nodes = proTree.getNodes();
		for (Node node : nodes) {
			String tempIdf = node.getId();
			if (tempIdf.equals(idf)) {
				return node;
			}
		}
		return null;
	}

	// ��ȡ��nodeΪ������������ڵ�
	public List<Node> getDesc(ProTree proTree, String nodeIdf) {
		List<Node> desc = new ArrayList<Node>();
		Node node = getNodeById(proTree, nodeIdf);
		desc.add(node);// Note:�����Լ�
		Queue<Node> queue = new LinkedList<>();
		List<String> chaNodes = node.getChaNodes();
		for (String chaNodeIdf : chaNodes) {
			Node chaNode = getNodeById(proTree, chaNodeIdf);
			desc.add(chaNode);
			queue.add(chaNode);
		}
		while (queue.size() > 0) {
			Node tempNode = queue.poll();
			if (tempNode.getType().equals("leaf")) {
				continue;
			}
			List<String> descNodes = tempNode.getChaNodes();
			for (String descIdf : descNodes) {
				Node desdNode = getNodeById(proTree, descIdf);
				desc.add(desdNode);
				queue.add(desdNode);
			}
		}
		return desc;
	}

	// ��ȡ���׽ڵ�
	public Node getFatherNode(ProTree proTree, Node node) {
		List<Node> nodes = proTree.getNodes();
		for (Node tempNode : nodes) {
			List<String> chaNodes = tempNode.getChaNodes();
			if (chaNodes.contains(node.getId())) {
				return tempNode;
			}
		}
		return null;
	}

	// ��ȡ���׽ڵ�
	public Node getFatherNode(ProTree proTree, String nodeId) {
		List<Node> nodes = proTree.getNodes();
		for (Node tempNode : nodes) {
			List<String> chaNodes = tempNode.getChaNodes();
			if (chaNodes.contains(nodeId)) {
				return tempNode;
			}
		}
		return null;
	}

	// �ж��Ƿ���˳����е�һ���ڵ�
	public boolean isFirstNodeInSEQ(Node fatherNode, Node node) {
		List<String> chaNodes = fatherNode.getChaNodes();
		if (chaNodes.get(0).equals(node.getId())) {
			return true;
		}
		return false;
	}

	// �ж��Ƿ���˳����е�һ���ڵ�
	public boolean isFirstNodeInSEQ(Node fatherNode, String nodeId) {
		List<String> chaNodes = fatherNode.getChaNodes();
		if (chaNodes.get(0).equals(nodeId)) {
			return true;
		}
		return false;
	}

	// �ж�node�Ƿ�Ϊ���ӽڵ�
	public boolean isChaNode(List<Node> chaNodes, Node node) {
		for (Node chaNode : chaNodes) {
			if (chaNode.getId().equals(node.getId())) {
				return true;
			}
		}
		return false;
	}

	// �ж�proTree�Ƿ���Էֽ�,������XOR�ڵ�
	public Node isDecompose(ProTree proTree) {
		List<Node> nodes = proTree.getNodes();
		int size = nodes.size();
		// Note:�Ӹ���ʼ����,���������ظ���Ƭ��(����B31)
		for (int i = size - 1; i >= 0; i--) {
			Node node = nodes.get(i);
			String type = node.getType();
			if (type.equals("XOR")) {
				return node;
			}
		}
		return null;
	}

	// ��ȡproTree��SEQ�ڵ㼯
	public List<Node> getSEQNode(ProTree proTree) {
		List<Node> SEQNodes = new ArrayList<Node>();
		List<Node> nodes = proTree.getNodes();
		for (Node node : nodes) {
			String type = node.getType();
			if (type.equals("SEQ")) {
				SEQNodes.add(node);
			}
		}
		return SEQNodes;
	}

}
