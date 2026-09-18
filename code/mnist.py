# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.23.3",
#     "matplotlib>=3.11.2",
#     "numpy>=2.5.2",
#     "qiskit>=2.5.2",
#     "qiskit-machine-learning>=0.9.1",
#     "torch>=2.5.1",
#     "torchvision>=0.20.1",
# ]
# [[tool.uv.index]]
# name = "pytorch"
# url = "https://download.pytorch.org/whl/cu121"
#
# [tool.uv.sources]
# torch = { index = "pytorch" }
# torchvision = { index = "pytorch" }
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App()


@app.cell
def _():
    import matplotlib.pyplot as plt
    import numpy as np
    import torch
    import torch.nn.functional as F
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import real_amplitudes, zz_feature_map
    from qiskit.primitives import StatevectorEstimator as Estimator
    from qiskit_machine_learning.connectors import TorchConnector
    from qiskit_machine_learning.neural_networks import EstimatorQNN
    from qiskit_machine_learning.utils import algorithm_globals
    from torch import cat, manual_seed, no_grad, optim
    from torch.nn import (
    	Conv2d,
    	Dropout2d,
    	Linear,
    	Module,
    	NLLLoss,
    )
    from torch.utils.data import DataLoader
    from torchvision import datasets, transforms

    print('PyTorch:', torch.__version__)
    print('CUDA:', torch.cuda.is_available())
    print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')

    algorithm_globals.random_seed = 42
    estimator = Estimator()

    return (
        Conv2d,
        DataLoader,
        Dropout2d,
        EstimatorQNN,
        F,
        Linear,
        Module,
        NLLLoss,
        QuantumCircuit,
        TorchConnector,
        datasets,
        estimator,
        manual_seed,
        no_grad,
        np,
        optim,
        plt,
        real_amplitudes,
        torch,
        transforms,
        zz_feature_map,
    )


@app.cell
def _(DataLoader, datasets, manual_seed, np, transforms):
    # Train Dataset
    # -------------

    # Set train shuffle seed (for reproducibility)
    manual_seed(42)

    batch_size = 1
    n_samples_train = 1000

    # Use pre-defined torchvision function to load MNIST train data
    X_train = datasets.MNIST(
    	root="./data", train=True, download=True, transform=transforms.Compose([transforms.ToTensor()])
    )

    # Filter out labels (originally 0-9), leaving only labels 0, 1 and 2
    n_labels = 4

    def filter_data(data, nb_samples):
        idx = np.concatenate([
            np.where(data.targets == label)[0][:nb_samples]
            for label in range(n_labels)
        ])

        data.data = data.data[idx]
        data.targets = data.targets[idx]

    filter_data(X_train, n_samples_train)

    # Define torch dataloader with filtered data
    train_loader = DataLoader(X_train, batch_size=batch_size, shuffle=True)
    return batch_size, filter_data, n_labels, train_loader


@app.cell
def _(plt, train_loader):
    n_samples_show = 6

    data_iter = iter(train_loader)
    fig, axes = plt.subplots(nrows=1, ncols=n_samples_show, figsize=(10, 3))

    while n_samples_show > 0:
    	images, targets = data_iter.__next__()

    	axes[n_samples_show - 1].imshow(images[0, 0].numpy().squeeze(), cmap="gray")
    	axes[n_samples_show - 1].set_xticks([])
    	axes[n_samples_show - 1].set_yticks([])
    	axes[n_samples_show - 1].set_title(f"Labeled: {targets[0].item()}")

    	n_samples_show -= 1

    plt.show()
    return


@app.cell
def _(DataLoader, batch_size, datasets, filter_data, transforms):
    # Test Dataset
    # -------------

    # Set test shuffle seed (for reproducibility)
    # manual_seed(5)

    n_samples_test = 50

    # Use pre-defined torchvision function to load MNIST test data
    X_test = datasets.MNIST(
    	root="./data", train=False, download=True, transform=transforms.Compose([transforms.ToTensor()])
    )

    # Filter out labels (originally 0-9), leaving only labels 0 and 1
    filter_data(X_test, n_samples_test)

    # Define torch dataloader with filtered data
    test_loader = DataLoader(X_test, batch_size=batch_size, shuffle=True)
    return (test_loader,)


@app.cell
def _(
    EstimatorQNN,
    QuantumCircuit,
    estimator,
    n_labels,
    real_amplitudes,
    zz_feature_map,
):
    # Define and create QNN
    def create_qnn():
    	feature_map = zz_feature_map(n_labels)
    	ansatz = real_amplitudes(n_labels, reps=1)
    	qc = QuantumCircuit(n_labels)	
    	qc.compose(feature_map, inplace=True)
    	qc.compose(ansatz, inplace=True)

    	# REMEMBER TO SET input_gradients=True FOR ENABLING HYBRID GRADIENT BACKPROP
    	qnn = EstimatorQNN(
    		circuit=qc,
    		input_params=list(feature_map.parameters),
    		weight_params=list(ansatz.parameters),
    		input_gradients=True,
    		estimator=estimator,
    	)
    	return qnn

    qnn = create_qnn()
    return (qnn,)


@app.cell
def _(
    Conv2d,
    Dropout2d,
    F,
    Linear,
    Module,
    NLLLoss,
    TorchConnector,
    n_labels,
    optim,
    qnn,
    train_loader,
):
    class Net(Module):
        def __init__(self, qnn):
            super().__init__()
            self.conv1 = Conv2d(1, 2, kernel_size=5)
            self.conv2 = Conv2d(2, 16, kernel_size=5)
            self.dropout = Dropout2d()
            self.fc1 = Linear(256, 64)
            self.fc2 = Linear(64, n_labels)
            self.qnn = TorchConnector(qnn)
            self.fc3 = Linear(1, n_labels)

        def forward(self, x):
            x = F.relu(self.conv1(x))
            x = F.max_pool2d(x, 2)
            x = F.relu(self.conv2(x))
            x = F.max_pool2d(x, 2)
            x = self.dropout(x)
            x = x.view(x.shape[0], -1)
            x = F.relu(self.fc1(x))
            x = self.fc2(x)
            x = self.qnn(x)
            x = self.fc3(x)
            return F.log_softmax(x, dim=1)

    model = Net(qnn)

    optimizer = optim.Adam(model.parameters(), lr=0.001)
    loss_func = NLLLoss()

    epochs = 10
    loss_list = []
    model.train()

    for epoch in range(epochs):
    	total_loss = []

    	for batch_idx, (data, target) in enumerate(train_loader):
    		optimizer.zero_grad(set_to_none=True)
    		output = model(data)
    		loss = loss_func(output, target)
    		loss.backward()
    		optimizer.step()
    		total_loss.append(loss.item())

    	loss_list.append(sum(total_loss) / len(total_loss))

    	print(f"Training [{100.0 * (epoch + 1) / epochs:.0f}%]\t Loss: {loss_list[-1]:.4f}")
    return loss_func, loss_list, model, total_loss


@app.cell
def _(loss_list, model, plt, torch):
    plt.plot(loss_list)
    plt.title("Hybrid NN Training Convergence")
    plt.xlabel("Training Iterations")
    plt.ylabel("Neg. Log Likelihood Loss")
    plt.show()

    torch.save(model.state_dict(), "model.pt")
    return


@app.cell
def _(batch_size, loss_func, model, no_grad, test_loader, total_loss):
    # qnn = create_qnn()
    # model = Net(qnn)
    # model.load_state_dict(torch.load("model.pt"))

    def test_model():
    	model.eval()

    	with no_grad():
    		correct = 0

    		for batch_idx, (data, target) in enumerate(test_loader):
    			output = model(data)

    			if len(output.shape) == 1:
    				output = output.reshape(1, *output.shape)

    			pred = output.argmax(dim=1, keepdim=True)
    			correct += pred.eq(target.view_as(pred)).sum().item()

    			loss = loss_func(output, target)
    			total_loss.append(loss.item())

    		print(
    			f"Performance on test data:\n\t Loss: {sum(total_loss) / len(total_loss):.4f}\n\t Accuracy: {correct / len(test_loader) / batch_size * 100:.1f}%"
    		)

    test_model()
    return


@app.cell
def _(model, no_grad, plt, test_loader):
    def plot_test_results():
    	n_samples_show = 6
    	count = 0

    	fig, axes = plt.subplots(nrows=1, ncols=n_samples_show, figsize=(10, 3))

    	model.eval()

    	with no_grad():
    		for batch_idx, (data, target) in enumerate(test_loader):
    			if count == n_samples_show:
    				break

    			output = model(data[0:1])

    			if len(output.shape) == 1:
    				output = output.reshape(1, *output.shape)

    			pred = output.argmax(dim=1, keepdim=True)

    			axes[count].imshow(data[0].numpy().squeeze(), cmap="gray")
    			axes[count].set_xticks([])
    			axes[count].set_yticks([])
    			axes[count].set_title(f"Predicted {pred.item()}")

    			count += 1
	
    	plt.show()

    plot_test_results()
    return


if __name__ == "__main__":
    app.run()
