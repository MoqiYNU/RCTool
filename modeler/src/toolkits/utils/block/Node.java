package toolkits.utils.block;

import java.util.ArrayList;
import java.util.List;

/**
 * @author Moqi
 * ����������нڵ�(����idf,�ڵ����ͼ����ӽڵ�)
 */
public class Node {
	
	private String id;
	private String type;
	//Note:���ӽ����id��ʶ
	private List<String> chaNodes;
	
	public Node() {
		chaNodes = new ArrayList<>();
	}
	
	/****************************Utils����******************************/
	
	//��Ӻ��ӽڵ�(�����ظ����)
	public void addChaNode(String node) {
		if (!chaNodes.contains(node)) {
			chaNodes.add(node);
		}
	}
	public void addChaNodes(List<String> nodes) {
		for (String node : nodes) {
			if (!chaNodes.contains(node)) {
				chaNodes.add(node);
			}
		}
	}
	
	/*************************Get��Set����****************************/
	
	public String getId() {
		return id;
	}
	public void setId(String idf) {
		this.id = idf;
	}
	public String getType() {
		return type;
	}
	public void setType(String type) {
		this.type = type;
	}
	public List<String> getChaNodes() {
		return chaNodes;
	}
	public void setChaNodes(List<String> chaNodes) {
		this.chaNodes = chaNodes;
	}

}
