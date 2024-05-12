package pipe.gui.action;

import java.awt.Container;
import java.awt.event.ActionEvent;

import javax.swing.AbstractAction;

import pipe.dataLayer.Place;
import pipe.gui.CreateGui;

@SuppressWarnings("serial")
public class SetResPlaceAction extends AbstractAction {

	@SuppressWarnings("unused")
	private Container contentPane;
	private Place selected;

	public SetResPlaceAction(Container contentPane, Place place) {
		this.contentPane = contentPane;
		selected = place;
	}

	@Override
	public void actionPerformed(ActionEvent e) {
		
		// 1. ��selected����Ϣ����,����ȡ��������
		if (selected.isMsgPlace() == true) {
			selected.setMsgPlace(false);
			// �Ƴ�ѡ�������Id
			CreateGui.getModel().removeMsgPlace(selected.getId());
		}
		// 2. ����selectedΪ��Դ����
		selected.setResPlace(true);
		// ���ѡ�������Id
		CreateGui.getModel().addResPlace(selected.getId());
		// �ػ浱ǰ����
		selected.repaint();
		
	}

}
