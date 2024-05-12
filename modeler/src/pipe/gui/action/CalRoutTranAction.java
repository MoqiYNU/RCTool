package pipe.gui.action;

import java.awt.Container;
import java.awt.event.ActionEvent;

import javax.swing.AbstractAction;

import pipe.dataLayer.Transition;
import pipe.gui.CreateGui;

@SuppressWarnings("serial")
public class CalRoutTranAction extends AbstractAction {

	@SuppressWarnings("unused")
	private Container contentPane;
	private Transition selected;

	public CalRoutTranAction(Container contentPane, Transition transition) {
		this.contentPane = contentPane;
		selected = transition;
	}

	@Override
	public void actionPerformed(ActionEvent arg0) {
		selected.setRoutTran(false);
		// �Ƴ�ѡ��·�ɱ�Ǩ��Id
		CreateGui.getModel().removeRoutTran(selected.getId());
		// �ػ浱ǰ��Ǩ
		selected.repaint();
	}

}
