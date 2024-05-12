package pipe.gui.action;

import java.awt.Container;
import java.awt.event.ActionEvent;

import javax.swing.AbstractAction;

import pipe.dataLayer.Place;
import pipe.gui.CreateGui;

@SuppressWarnings("serial")
public class SetMsgPlaceAction extends AbstractAction {

	@SuppressWarnings("unused")
	private Container contentPane;
	private Place selected;

	public SetMsgPlaceAction(Container contentPane, Place place) {
		this.contentPane = contentPane;
		selected = place;
	}

	@Override
	public void actionPerformed(ActionEvent e) {
		
		// 1. ��selected����Դ����,����ȡ��������
		if (selected.isResPlace() == true) {
			selected.setResPlace(false);
			// ���ѡ�������Id
			CreateGui.getModel().removeResPlace(selected.getId());
		}
		// 2. ����selectedΪ��Ϣ����
		selected.setMsgPlace(true);
		// ���ѡ�������Id
		CreateGui.getModel().addMsgPlace(selected.getId());
		// �ػ浱ǰ����
		selected.repaint();
		
	}

}
