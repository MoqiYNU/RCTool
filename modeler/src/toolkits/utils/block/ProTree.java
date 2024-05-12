package toolkits.utils.block;

import java.util.ArrayList;
import java.util.List;

import org.apache.commons.collections4.MultiValuedMap;
import org.apache.commons.collections4.multimap.ArrayListValuedHashMap;

/**
 * *@author Moqi
 * ���������,�����ڵ㼰�亢�ӽڵ㼯
 */
public class ProTree {

	private List<Node> nodes;
	// ��ֵӳ��洢�������е�ͬ������
	private MultiValuedMap<String, String> links;
	// �洢�ڲ���Լ��Ǩ(�ȷǿ��Ʊ�ǨҲ�ǽ�����Ǩ)
	private List<String> innerTrans;

	public ProTree() {
		nodes = new ArrayList<>();
		links = new ArrayListValuedHashMap<>();
		innerTrans = new ArrayList<>();
	}

	/**************************** Utils���� ******************************/

	public void addNode(Node node) {
		if (!isExistingNode(node.getId(), nodes)) {
			nodes.add(node);
		}
	}

	public void addNodes(List<Node> addNodes) {
		for (Node addNode : addNodes) {
			if (!isExistingNode(addNode.getId(), nodes)) {
				nodes.add(addNode);
			}
		}
	}

	// ����ڲ���Ǩ
	public void addInnerTran(String tran) {
		if (!innerTrans.contains(tran)) {
			innerTrans.add(tran);
		}
	}

	// �жϽ���Ƿ����
	public boolean isExistingNode(String id, List<Node> nodes) {
		for (Node node : nodes) {
			if (id.equals(node.getId())) {
				return true;
			}
		}
		return false;
	}

	// �Ƴ����нڵ�node
	public void removeNode(Node node) {
		for (int i = 0; i < nodes.size(); i++) {
			Node tempNode = nodes.get(i);
			if (tempNode.getId().equals(node.getId())) {
				nodes.remove(i);
				break;
			}
		}
	}

	/************************* Get��Set���� ****************************/

	public List<Node> getNodes() {
		return nodes;
	}

	public void setNodes(List<Node> nodes) {
		this.nodes = nodes;
	}

	public MultiValuedMap<String, String> getLinks() {
		return links;
	}

	public void setLinks(MultiValuedMap<String, String> links) {
		this.links = links;
	}

	public List<String> getInnerTrans() {
		return innerTrans;
	}

	public void setInnerTrans(List<String> innerTrans) {
		this.innerTrans = innerTrans;
	}

}
